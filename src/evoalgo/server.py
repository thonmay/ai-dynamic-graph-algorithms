"""Web UI server: run list, candidate files, live event stream, control.

Binds to 127.0.0.1 by default and has no authentication: access is expected
through an SSH port-forward. Requests that carry a browser Origin header from
a non-local site are refused, so a web page open in the same browser cannot
steer or launch runs.

Websocket protocol (``/api/runs/{run_id}/ws?from=N``):
  server -> client  every event from events.jsonl with seq >= N (backlog,
                    then live), plus {"type": "queued"|"error", ...} replies
  client -> server  a control command, e.g. {"cmd": "pause"},
                    {"cmd": "hint", "text": "..."},
                    {"cmd": "set", "field": "population_size", "value": 4}
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import RunConfig
from .events import EVENTS_FILE, read_events, send_command, validate_command

RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
CANDIDATE_ID = re.compile(r"^gen\d{3}_c\d{2}$")
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
STATIC_DIR = Path(__file__).parent / "ui_dist"
MAX_FILE_BYTES = 200_000
POLL_SECONDS = 0.5


def _origin_ok(origin: str | None) -> bool:
    """Allow non-browser clients (no Origin) and pages served from localhost."""
    if not origin:
        return True
    return urlsplit(origin).hostname in LOCAL_HOSTS


def run_state(events: list[dict[str, Any]]) -> str:
    if not events:
        return "empty"
    if events[-1].get("type") == "run_end":
        return "done"
    paused = False
    for e in events:
        if e.get("type") == "control_ack":
            if e.get("cmd") == "pause":
                paused = True
            elif e.get("cmd") in ("resume", "stop"):
                paused = False
    return "paused" if paused else "running"


def summarize(run_dir: Path) -> dict[str, Any]:
    events = read_events(run_dir)
    summary: dict[str, Any] = {"run_id": run_dir.name, "has_events": bool(events),
                               "state": run_state(events) if events else "no_events"}
    if not events:
        return summary
    start = next((e for e in events if e["type"] == "run_start"), {})
    commits = [e for e in events if e["type"] == "gen_committed"]
    last = commits[-1] if commits else {}
    summary.update(
        problem=start.get("problem"), model=start.get("model"),
        max_generations=start.get("max_generations"),
        generation=last.get("gen", 0), best_id=last.get("best_id"),
        best_fitness=last.get("best_fitness"), best_work_ratio=last.get("best_work_ratio"),
        model_calls=last.get("model_calls"), started=start.get("ts"),
        updated=events[-1].get("ts"), events=len(events),
        history=[c.get("best_work_ratio") for c in commits],
    )
    return summary


def _read_capped(path: Path) -> str | None:
    try:
        with open(path, "rb") as f:
            return f.read(MAX_FILE_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return None


class LaunchRequest(BaseModel):
    config: str = Field(description="a config name returned by GET /api/configs")
    run_id: str | None = None
    max_generations: int | None = Field(None, ge=1, le=1000)
    population_size: int | None = Field(None, ge=1, le=50)
    model: str | None = Field(None, max_length=200)


def create_app(runs_root: Path | str, static_dir: Path | None = STATIC_DIR) -> FastAPI:
    root = Path(runs_root).resolve()
    app = FastAPI(title="evoalgo", docs_url=None, redoc_url=None)

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

    @app.post("/api/runs", status_code=201)
    def launch(req: LaunchRequest, request: Request) -> dict[str, Any]:
        if not _origin_ok(request.headers.get("origin")):
            raise HTTPException(403, "cross-site request refused")
        template = config_files().get(req.config)
        if template is None:
            raise HTTPException(404, "unknown config")
        config = RunConfig.load(template)
        for field in ("max_generations", "population_size", "model"):
            value = getattr(req, field)
            if value is not None:
                setattr(config, field, value)
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
        with open(launch_dir / f"{run_id}.log", "ab") as log:
            proc = subprocess.Popen(
                [sys.executable, "-m", "evoalgo.cli", "start", str(config_path),
                 "--run-id", run_id],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        return {"run_id": run_id, "pid": proc.pid}

    @app.websocket("/api/runs/{run_id}/ws")
    async def stream(websocket: WebSocket, run_id: str,
                     since: int = Query(0, alias="from", ge=0)) -> None:
        if not _origin_ok(websocket.headers.get("origin")):
            await websocket.close(code=1008)
            return
        try:
            run_dir = run_dir_for(run_id)
        except HTTPException:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        tasks = [asyncio.create_task(_tail(websocket, run_dir / EVENTS_FILE, since)),
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


async def _tail(ws: WebSocket, path: Path, since: int) -> None:
    """Send events with seq >= since, then follow the file as it grows."""
    offset, buf = 0, b""
    while True:
        try:
            size = os.stat(path).st_size
        except FileNotFoundError:
            size = 0
        if size < offset:  # file was rebuilt (events backfill --force)
            offset, buf = 0, b""
        if size > offset:
            with open(path, "rb") as f:
                f.seek(offset)
                chunk = f.read(size - offset)
            offset += len(chunk)
            *lines, buf = (buf + chunk).split(b"\n")
            for raw in lines:
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict) and event.get("seq", -1) >= since:
                    await ws.send_json(event)
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
        if error:
            await ws.send_json({"type": "error", "reason": error})
            continue
        record = send_command(run_dir, **command)
        await ws.send_json({"type": "queued", "cmd_id": record["id"], "cmd": record["cmd"]})
