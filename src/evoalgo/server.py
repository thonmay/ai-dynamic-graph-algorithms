# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Web UI server: run list, candidate files, live event stream, control.

Binds to 127.0.0.1 by default. Loopback is not a trust boundary on a shared
host (every local user can connect), so every /api request and the websocket
need an access token: generated at start-up, printed once as a link
(``/?token=...``) that sets an HttpOnly cookie; scripts send it as
``Authorization: Bearer <token>``. Requests that carry a browser Origin header
from a non-local site are refused as well, so a web page open in the same
browser cannot steer or launch runs.

Websocket protocol (``/api/runs/{run_id}/ws?from=N``):
  server -> client  first {"type": "pending", "commands": [...]} (commands not
                    yet acknowledged), then every event from events.jsonl with
                    seq >= N (backlog, then live), {"type": "engine",
                    "state": "alive"|"gone"|"none"} at connect and on change,
                    and {"type": "queued"|"error", ...} replies
  client -> server  a control command, e.g. {"cmd": "pause"},
                    {"cmd": "hint", "text": "..."},
                    {"cmd": "set", "field": "population_size", "value": 4}
"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import MAX_GOAL_CHARS, RunConfig
from .packs import PackError, find_packs, pack_info, resolve_pack
from .events import (
    engine_state,
    summarize,
    EVENTS_FILE,
    pending_commands,
    read_events,
    send_command,
    validate_command,
)

RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
CANDIDATE_ID = re.compile(r"^gen\d{3}_c\d{2}$")
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
STATIC_DIR = Path(__file__).parent / "ui_dist"
MAX_FILE_BYTES = 200_000
POLL_SECONDS = 0.5


def _origin_ok(origin: str | None, host: str | None = None) -> bool:
    """Allow non-browser clients (no Origin) and pages of this server only.

    The port counts: a page another local user serves on localhost:9999 is a
    different origin, though cookies (and SameSite) ignore the port.
    """
    if not origin:
        return True
    parts = urlsplit(origin)
    if parts.hostname not in LOCAL_HOSTS:
        return False
    return host is None or parts.netloc == host


TOKEN_COOKIE = "evoalgo_token"  # + "_<port>": one cookie per server
UNAUTHORIZED = "missing or wrong access token: open the link printed by `evoalgo ui`"


def _token_ok(expected: str, given: str | None) -> bool:
    return given is not None and hmac.compare_digest(expected.encode(), given.encode())


def _request_token_ok(expected: str, conn: Request | WebSocket) -> bool:
    """Cookie (browser) or ``Authorization: Bearer`` (scripts)."""
    auth = conn.headers.get("authorization", "")
    bearer = auth[7:] if auth.lower().startswith("bearer ") else None
    return _token_ok(expected, conn.cookies.get(_cookie_name(conn))) or _token_ok(expected, bearer)


def _cookie_name(conn: Request | WebSocket) -> str:
    return f"{TOKEN_COOKIE}_{conn.url.port or 80}"


def _read_capped(path: Path) -> str | None:
    try:
        with open(path, "rb") as f:
            return f.read(MAX_FILE_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return None


class LaunchRequest(BaseModel):
    """Start a run from a problem pack (UI) or a config template (CLI parity).

    Exactly one of ``pack`` and ``config`` must be given.
    """
    pack: str | None = Field(None, description="a pack name returned by GET /api/packs")
    config: str | None = Field(None, description="a config name returned by GET /api/configs")
    research_goal: str | None = Field(None, max_length=MAX_GOAL_CHARS)
    run_id: str | None = None
    max_generations: int | None = Field(None, ge=1, le=1000)
    population_size: int | None = Field(None, ge=1, le=50)
    model_call_budget: int | None = Field(None, ge=1, le=100_000)
    model: str | None = Field(None, max_length=200)
    # Named endpoints only: a free URL plus a free key-variable name would let
    # anyone who reaches this unauthenticated port send a token elsewhere.
    # Custom URLs stay available through config YAML.
    provider: Literal["api", "opencode"] | None = None
    endpoint: Literal["openrouter", "openai"] | None = None
    n_max: int | None = Field(None, ge=2, le=8)
    early_stop_on_success: bool | None = None
    dynamic_agents: bool | None = None


# Defaults for a pack launch; a pack has no config template of its own.
PACK_DEFAULTS = {"max_generations": 10, "population_size": 4, "model_call_budget": 200,
                 "elitism_k": 1, "early_stop_on_success": False}


ENDPOINT_LABELS = {"openrouter": "OpenRouter", "openai": "OpenAI"}


def agent_options() -> dict[str, Any]:
    """What the new-run page may offer: endpoints with key presence, harness binary.

    Only says whether a key is present; never returns it.
    """
    from .agents.api import ENDPOINTS, _read_key
    from .agents.harness import OpencodeBackend
    endpoints = [{"id": name, "label": ENDPOINT_LABELS[name], "key_env": env,
                  "key_set": bool(_read_key(env)), "model": None}
                 for name, (_url, env) in ENDPOINTS.items() if name in ENDPOINT_LABELS]
    harness = shutil.which(OpencodeBackend.find_bin(None))
    return {"endpoints": endpoints,
            "harness": {"id": "opencode", "available": bool(harness and os.access(harness, os.X_OK))}}


def create_app(runs_root: Path | str, static_dir: Path | None = STATIC_DIR,
               packs_root: Path | str | None = None, token: str | None = None) -> FastAPI:
    """The app. ``token`` None disables the access check (tests only)."""
    root = Path(runs_root).resolve()
    if packs_root is None:
        from .packs import DEFAULT_PROBLEMS_ROOT as packs_root
    app = FastAPI(title="evoalgo", docs_url=None, redoc_url=None)

    if token is not None:
        @app.middleware("http")
        async def require_token(request: Request, call_next):
            if request.query_params.get("token") is not None and request.url.path == "/":
                # The link printed at start-up: trade the query token for a
                # cookie and drop it from the address bar.
                if not _token_ok(token, request.query_params.get("token")):
                    return JSONResponse({"detail": UNAUTHORIZED}, status_code=401)
                response = RedirectResponse("/", status_code=303)
                response.set_cookie(_cookie_name(request), token, httponly=True, samesite="strict")
                return response
            if request.url.path.startswith("/api") and not _request_token_ok(token, request):
                return JSONResponse({"detail": UNAUTHORIZED}, status_code=401)
            return await call_next(request)

    def run_dir_for(run_id: str) -> Path:
        if not RUN_ID.match(run_id):
            raise HTTPException(404, "unknown run")
        path = (root / run_id).resolve()
        if path.parent != root or not (path / "config.yaml").is_file():
            raise HTTPException(404, "unknown run")
        return path

    def config_files() -> dict[str, Path]:
        """Templates for new runs: top-level *.yaml and each run's config.yaml."""
        found = {p.name: p for p in sorted(root.glob("*.yaml"))}
        for p in sorted(root.glob("*/config.yaml")):
            if RUN_ID.match(p.parent.name):
                found[f"{p.parent.name}/config.yaml"] = p
        return found

    @app.get("/api/runs")
    def list_runs() -> list[dict[str, Any]]:
        runs = [summarize(p.parent) for p in root.glob("*/config.yaml")
                if RUN_ID.match(p.parent.name)]
        return sorted(runs, key=lambda r: r.get("updated") or "", reverse=True)

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        run_dir = run_dir_for(run_id)
        summary = summarize(run_dir)
        summary["config"] = RunConfig.load(run_dir / "config.yaml").to_dict()
        summary["pending"] = pending_commands(run_dir)
        return summary

    @app.get("/api/runs/{run_id}/candidates/{candidate_id}")
    def get_candidate(run_id: str, candidate_id: str) -> dict[str, Any]:
        run_dir = run_dir_for(run_id)
        if not CANDIDATE_ID.match(candidate_id):
            raise HTTPException(404, "unknown candidate")
        code = _read_capped(run_dir / "candidates" / f"{candidate_id}.py")
        if code is None:
            raise HTTPException(404, "unknown candidate")
        reflection = _read_capped(run_dir / "reflections" / f"{candidate_id}.md")
        return {"id": candidate_id, "code": code, "reflection": reflection}

    @app.get("/api/configs")
    def list_configs() -> list[str]:
        return list(config_files())

    @app.get("/api/packs")
    def list_packs() -> list[dict[str, Any]]:
        tiers = {"calibration": 0, "core": 1, "open": 2}
        return sorted((pack_info(p) for p in find_packs(packs_root)),
                      key=lambda p: (tiers.get(p["tier"], 9), p["name"]))

    @app.get("/api/agents")
    def list_agents() -> dict[str, Any]:
        return agent_options()

    @app.post("/api/runs", status_code=201)
    def launch(req: LaunchRequest, request: Request) -> dict[str, Any]:
        if not _origin_ok(request.headers.get("origin"), request.headers.get("host")):
            raise HTTPException(403, "cross-site request refused")
        if (req.pack is None) == (req.config is None):
            raise HTTPException(422, "give exactly one of 'pack' or 'config'")
        if req.pack is not None:
            # A name under packs_root only (resolve_pack also takes paths).
            if not RUN_ID.match(req.pack) or not (Path(packs_root) / req.pack).is_dir():
                raise HTTPException(404, "unknown pack")
            try:
                pack = resolve_pack(req.pack, packs_root)
            except (PackError, NotImplementedError) as e:
                raise HTTPException(404 if isinstance(e, PackError) else 422, str(e))
            config = RunConfig(pack=pack.name, problem=pack.checker, **PACK_DEFAULTS)
        else:
            template = config_files().get(req.config)
            if template is None:
                raise HTTPException(404, "unknown config")
            config = RunConfig.load(template)
        for field in ("max_generations", "population_size", "model_call_budget", "model",
                      "early_stop_on_success", "dynamic_agents"):
            value = getattr(req, field)
            if value is not None:
                setattr(config, field, value)
        if req.provider is not None:
            config.provider = req.provider
        if req.endpoint is not None:
            if config.provider != "api":
                raise HTTPException(422, "endpoint is only used with provider 'api'")
            # The endpoint's own key variable; a template's override is dropped.
            config.api_base_url, config.api_key_env, config.api_ca_cert = req.endpoint, None, None
        if req.n_max is not None:
            config.bound.n_max = req.n_max
        goal = (req.research_goal or "").strip()
        if goal:
            config.research_goal = goal
        config.elitism_k = min(config.elitism_k, config.population_size)
        config.workdir = str(root)
        errors = config.validate()
        if errors:
            raise HTTPException(422, "; ".join(errors))
        run_id = req.run_id or time.strftime("run_%Y%m%d_%H%M%S")
        if not RUN_ID.match(run_id):
            raise HTTPException(422, "run_id may only contain letters, digits, '.', '_', '-'")
        if (root / run_id).exists():
            raise HTTPException(409, f"run {run_id} already exists")

        launch_dir = root / ".launch"
        launch_dir.mkdir(exist_ok=True)
        config_path = launch_dir / f"{run_id}.yaml"
        config.save(config_path)
        # The run folder exists before the response: the UI opens the run's
        # stream right away, and the engine starts writing only after its
        # imports (~1 s), so an absent folder would refuse the first connect.
        (root / run_id).mkdir()
        config.save(root / run_id / "config.yaml")
        try:
            with open(launch_dir / f"{run_id}.log", "ab") as log:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "evoalgo.cli", "start", str(config_path),
                     "--run-id", run_id],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
        except OSError:
            shutil.rmtree(root / run_id, ignore_errors=True)
            raise
        return {"run_id": run_id, "pid": proc.pid}

    @app.websocket("/api/runs/{run_id}/ws")
    async def stream(websocket: WebSocket, run_id: str,
                     since: int = Query(0, alias="from", ge=0)) -> None:
        if not _origin_ok(websocket.headers.get("origin"), websocket.headers.get("host")) or (
                token is not None and not _request_token_ok(token, websocket)):
            await websocket.close(code=1008)
            return
        try:
            run_dir = run_dir_for(run_id)
        except HTTPException:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        # Unacknowledged commands first, so a reconnecting UI shows "pausing" etc.
        await websocket.send_json({"type": "pending", "commands": pending_commands(run_dir)})
        tasks = [asyncio.create_task(_tail(websocket, run_dir, since)),
                 asyncio.create_task(_commands(websocket, run_dir))]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception()
            if exc is not None and not isinstance(exc, WebSocketDisconnect):
                raise exc

    if static_dir is not None and (static_dir / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="ui")
    else:
        @app.get("/")
        def no_ui() -> dict[str, str]:
            return {"detail": "UI not built; the API is under /api"}

    return app


async def _tail(ws: WebSocket, run_dir: Path, since: int) -> None:
    """Send events with seq >= since, then follow the file as it grows.

    Also sends {"type": "engine"} on every liveness change, ordered so the UI
    never sees a live run without a live engine: the engine writes
    engine.json before its first event and removes it after its last one, so
    "alive" goes out before the events it covers and a lost engine after the
    final events it wrote.
    """
    path = run_dir / EVENTS_FILE
    offset, buf = 0, b""
    last_engine: str | None = None

    def read_new() -> list[dict[str, Any]]:
        nonlocal offset, buf
        try:
            size = os.stat(path).st_size
        except FileNotFoundError:
            size = 0
        if size < offset:  # file was rebuilt (events backfill --force)
            offset, buf = 0, b""
        if size <= offset:
            return []
        with open(path, "rb") as f:
            f.seek(offset)
            chunk = f.read(size - offset)
        offset += len(chunk)
        *lines, buf = (buf + chunk).split(b"\n")
        out = []
        for raw in lines:
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict) and event.get("seq", -1) >= since:
                out.append(event)
        return out

    while True:
        events = read_new()
        engine = engine_state(run_dir)
        if engine != last_engine and engine == "alive":
            await ws.send_json({"type": "engine", "state": engine})
            last_engine = engine
        for event in events:
            await ws.send_json(event)
        if engine != last_engine:
            # The engine may have appended run_end just before it exited.
            for event in read_new():
                await ws.send_json(event)
            await ws.send_json({"type": "engine", "state": engine})
            last_engine = engine
        await asyncio.sleep(POLL_SECONDS)


async def _commands(ws: WebSocket, run_dir: Path) -> None:
    """Queue control commands sent by the client."""
    while True:
        text = await ws.receive_text()
        try:
            message = json.loads(text)
        except json.JSONDecodeError:
            message = None
        if not isinstance(message, dict):
            await ws.send_json({"type": "error", "reason": "expected a JSON object"})
            continue
        command = {k: message[k] for k in ("cmd", "text", "field", "value") if k in message}
        error = validate_command(command)
        bounds = [e.get("type") for e in read_events(run_dir) if e.get("type") in ("run_start", "run_end")]
        if not error and bounds and bounds[-1] == "run_end":  # a resume adds a run_start
            # Nothing would read it; a later resume would apply a stale command.
            error = "the run has ended"
        if error:
            await ws.send_json({"type": "error", "reason": error})
            continue
        record = send_command(run_dir, **command)
        await ws.send_json({"type": "queued", "cmd_id": record["id"], "cmd": record["cmd"]})
