# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tests for the web UI server (HTTP API, websocket stream, control)."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from evoalgo import server  # noqa: E402
from evoalgo.events import CONTROL_FILE, ENGINE_FILE, EventLog, backfill, send_command  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SRC_RUN = REPO / "runs" / "mcs_pressure_e2e"


@pytest.fixture()
def runs(tmp_path, monkeypatch):
    if not SRC_RUN.exists():
        pytest.skip("reference run not present")
    run = tmp_path / "mcs_pressure_e2e"
    run.mkdir()
    for p in [SRC_RUN / "config.yaml", *SRC_RUN.glob("generation_*.json")]:
        shutil.copy(p, run / p.name)
    shutil.copytree(SRC_RUN / "candidates", run / "candidates",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SRC_RUN / "prompt_logs", run / "prompt_logs")
    backfill(run)
    (tmp_path / "bare").mkdir()
    shutil.copy(SRC_RUN / "config.yaml", tmp_path / "bare" / "config.yaml")
    monkeypatch.setattr(server, "POLL_SECONDS", 0.01)
    return tmp_path


@pytest.fixture()
def client(runs):
    return TestClient(server.create_app(runs, static_dir=None))


def test_list_and_get_run(client):
    runs = {r["run_id"]: r for r in client.get("/api/runs").json()}
    assert runs["bare"]["state"] == "no_events"
    r = runs["mcs_pressure_e2e"]
    assert r["state"] == "done" and r["generation"] == 5 and r["best_id"] == "gen003_c01"
    assert len(r["history"]) == 5
    detail = client.get("/api/runs/mcs_pressure_e2e").json()
    assert detail["config"]["problem"] == "dynamic_mcs"


def test_candidate_code(client):
    body = client.get("/api/runs/mcs_pressure_e2e/candidates/gen003_c01").json()
    assert "def _update" in body["code"] and body["reflection"] is None


@pytest.mark.parametrize("path", [
    "/api/runs/..%2F..%2Fetc",
    "/api/runs/nope",
    "/api/runs/mcs_pressure_e2e/candidates/..%2Fconfig",
    "/api/runs/mcs_pressure_e2e/candidates/gen009_c09",
])
def test_unknown_or_traversal_is_404(client, path):
    assert client.get(path).status_code == 404


def next_event(ws):
    """Next events.jsonl record, skipping pending/engine/reply messages."""
    while True:
        msg = ws.receive_json()
        if "seq" in msg:
            return msg


def next_of(ws, *types):
    while True:
        msg = ws.receive_json()
        if msg.get("type") in types:
            return msg


def test_websocket_backlog_from_offset_and_live(client, runs):
    with client.websocket_connect("/api/runs/mcs_pressure_e2e/ws?from=20") as ws:
        assert ws.receive_json() == {"type": "pending", "commands": []}
        first = next_event(ws)
        assert first["seq"] == 20
        rest = [next_event(ws) for _ in range(5)]
        assert rest[-1]["type"] == "run_end"
        EventLog(runs / "mcs_pressure_e2e").emit("note", text="live")
        live = next_event(ws)
        assert live["type"] == "note" and live["seq"] == 26


def test_websocket_control(client, runs):
    with client.websocket_connect("/api/runs/bare/ws") as ws:
        ws.send_json({"cmd": "set", "field": "population_size", "value": 0})
        assert next_of(ws, "queued", "error")["type"] == "error"
        ws.send_text("not json")
        assert next_of(ws, "queued", "error")["type"] == "error"
        ws.send_json({"cmd": "hint", "text": "try lazy repair", "extra": "dropped"})
        reply = next_of(ws, "queued", "error")
        assert reply["type"] == "queued" and reply["cmd"] == "hint"
    lines = (runs / "bare" / CONTROL_FILE).read_text().splitlines()
    assert len(lines) == 1 and '"extra"' not in lines[0]


def test_pending_commands_sent_first(client, runs):
    run = runs / "bare"
    acked = send_command(run, "pause")
    open_cmd = send_command(run, "hint", text="go lazy")
    EventLog(run).emit("control_ack", cmd_id=acked["id"], gen=1, cmd="pause")
    with client.websocket_connect("/api/runs/bare/ws") as ws:
        first = ws.receive_json()
    assert first["type"] == "pending"
    assert [c["id"] for c in first["commands"]] == [open_cmd["id"]]
    assert [c["id"] for c in client.get("/api/runs/bare").json()["pending"]] == [open_cmd["id"]]



def test_control_refused_on_ended_run(client, runs):
    EventLog(runs / "bare").emit("run_end", stop_reason="max_generations")
    with client.websocket_connect("/api/runs/bare/ws") as ws:
        ws.send_json({"cmd": "pause"})
        reply = next_of(ws, "queued", "error")
        assert reply == {"type": "error", "reason": "the run has ended"}
    assert not (runs / "bare" / CONTROL_FILE).exists()
    EventLog(runs / "bare").emit("run_start", resumed=True)  # `evoalgo resume`
    with client.websocket_connect("/api/runs/bare/ws") as ws:
        ws.send_json({"cmd": "pause"})
        assert next_of(ws, "queued", "error")["type"] == "queued"


def test_dashboard_escapes_script_end_in_llm_text(tmp_path):
    from evoalgo.dashboard import Dashboard
    html = Dashboard(tmp_path)._build_html(
        1, {"research_goal": "</script><script>alert(1)</script>"}, [], "r")
    assert "</script><script>alert(1)" not in html and "\\u003c/script>" in html

def _write_engine(run, pid):
    (run / ENGINE_FILE).write_text(json.dumps({"pid": pid, "host": socket.gethostname()}))


def test_engine_liveness_and_interrupted_state(client, runs):
    run = runs / "bare"
    EventLog(run).emit("run_start", run_id="bare", problem="dynamic_bfs")

    def state():
        r = next(r for r in client.get("/api/runs").json() if r["run_id"] == "bare")
        return r["engine"], r["state"]

    assert state() == ("none", "interrupted")
    _write_engine(run, os.getpid())
    assert state() == ("alive", "running")
    with client.websocket_connect("/api/runs/bare/ws") as ws:
        assert next_of(ws, "engine") == {"type": "engine", "state": "alive"}
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    _write_engine(run, child.pid)
    assert state() == ("gone", "interrupted")


def test_cross_site_origin_refused(client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/runs/bare/ws",
                                      headers={"origin": "https://evil.example"}) as ws:
            ws.receive_json()
    r = client.post("/api/runs", json={"config": "bare/config.yaml"},
                    headers={"origin": "https://evil.example"})
    assert r.status_code == 403


def test_list_packs(client):
    packs = client.get("/api/packs").json()
    names = [p["name"] for p in packs]
    assert {"dynamic_bfs", "dynamic_mcs", "dynamic_lbfs"} <= set(names)
    tiers = [p["tier"] for p in packs]
    assert tiers == sorted(tiers, key=["calibration", "core", "open"].index)
    mcs = next(p for p in packs if p["name"] == "dynamic_mcs")
    assert mcs["question"] and mcs["brief"] and mcs["directed"] is False


def test_launch_from_pack(client, runs, monkeypatch):
    calls = []

    class FakePopen:
        def __init__(self, cmd, **kw):
            calls.append(cmd)
            self.pid = 4243

    monkeypatch.setattr(server.subprocess, "Popen", FakePopen)
    body = {"pack": "dynamic_bfs", "run_id": "bfs_goal", "research_goal": "  avoid full recompute  ",
            "max_generations": 3, "population_size": 2, "model_call_budget": 20, "n_max": 4}
    r = client.post("/api/runs", json=body)
    assert r.status_code == 201, r.text
    from evoalgo.config import RunConfig
    cfg = RunConfig.load(runs / ".launch" / "bfs_goal.yaml")
    assert (cfg.pack, cfg.problem, cfg.research_goal) == ("dynamic_bfs", "dynamic_bfs", "avoid full recompute")
    assert (cfg.max_generations, cfg.population_size, cfg.model_call_budget, cfg.bound.n_max) == (3, 2, 20, 4)
    assert cfg.elitism_k <= cfg.population_size and cfg.early_stop_on_success is False
    # The run folder exists before the engine starts, so the UI's first
    # stream connect right after the launch is accepted.
    assert (runs / "bfs_goal" / "config.yaml").is_file()
    with client.websocket_connect("/api/runs/bfs_goal/ws") as ws:
        assert ws.receive_json()["type"] == "pending"
    assert client.post("/api/runs", json={"pack": "nope"}).status_code == 404
    assert client.post("/api/runs", json={"pack": "../dynamic_bfs"}).status_code == 404
    assert client.post("/api/runs", json={}).status_code == 422
    both = {"pack": "dynamic_bfs", "config": "bare/config.yaml"}
    assert client.post("/api/runs", json=both).status_code == 422
    long_goal = {"pack": "dynamic_bfs", "research_goal": "x" * 2001}
    assert client.post("/api/runs", json=long_goal).status_code == 422


def test_launch(client, runs, monkeypatch):
    calls = []

    class FakePopen:
        def __init__(self, cmd, **kw):
            calls.append(cmd)
            self.pid = 4242

    monkeypatch.setattr(server.subprocess, "Popen", FakePopen)
    assert "bare/config.yaml" in client.get("/api/configs").json()
    assert client.post("/api/runs", json={"config": "nope.yaml"}).status_code == 404
    assert client.post("/api/runs", json={"config": "bare/config.yaml",
                                          "run_id": "bare"}).status_code == 409
    assert client.post("/api/runs", json={"config": "bare/config.yaml",
                                          "run_id": "../x"}).status_code == 422
    r = client.post("/api/runs", json={"config": "bare/config.yaml", "run_id": "new_run",
                                       "max_generations": 2},
                    headers={"origin": "http://127.0.0.1:8765", "host": "127.0.0.1:8765"})
    assert r.status_code == 201 and r.json()["run_id"] == "new_run"
    other_port = client.post("/api/runs", json={"config": "bare/config.yaml", "run_id": "x2"},
                             headers={"origin": "http://127.0.0.1:9999", "host": "127.0.0.1:8765"})
    assert other_port.status_code == 403  # another local server is another origin
    cmd = calls[0]
    assert cmd[-2:] == ["--run-id", "new_run"] and cmd[2] == "evoalgo.cli"
    saved = (runs / ".launch" / "new_run.yaml").read_text()
    assert "max_generations: 2" in saved
    assert all(r["run_id"] != ".launch" for r in client.get("/api/runs").json())


def test_agent_options_never_leak_keys(client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-secret-value")
    r = client.get("/api/agents")
    assert r.status_code == 200
    assert "sk-secret-value" not in r.text
    ep = {e["id"]: e for e in r.json()["endpoints"]}
    assert set(ep) == {"openrouter", "openai"}
    assert ep["openrouter"]["key_set"] is True


def test_launch_with_api_endpoint(client, runs, monkeypatch):
    monkeypatch.setattr(server.subprocess, "Popen", lambda cmd, **kw: type("P", (), {"pid": 1})())
    body = {"pack": "dynamic_bfs", "run_id": "api_run", "provider": "api", "endpoint": "openrouter",
            "model": "qwen/qwen3-coder"}
    assert client.post("/api/runs", json=body).status_code == 201
    from evoalgo.config import RunConfig
    cfg = RunConfig.load(runs / ".launch" / "api_run.yaml")
    assert (cfg.provider, cfg.api_base_url, cfg.api_key_env, cfg.model) == \
        ("api", "openrouter", None, "qwen/qwen3-coder")
    # api without a model, an unknown endpoint, a free URL, or endpoint without api
    for bad in ({"provider": "api", "endpoint": "openai"},
                {"provider": "api", "endpoint": "evil", "model": "m"},
                {"provider": "api", "endpoint": "https://example.com/v1", "model": "m"},
                {"provider": "opencode", "endpoint": "openai"},
                {"provider": "mock"}):
        assert client.post("/api/runs", json={"pack": "dynamic_bfs", **bad}).status_code == 422, bad


def test_access_token(runs):
    from starlette.websockets import WebSocketDisconnect as WSDisconnect
    app = server.create_app(runs, static_dir=None, token="s3cret-token")
    anon = TestClient(app)
    assert anon.get("/api/runs").status_code == 401
    assert anon.get("/api/runs", headers={"authorization": "Bearer wrong"}).status_code == 401
    assert anon.get("/?token=wrong", follow_redirects=False).status_code == 401
    with pytest.raises(WSDisconnect):
        with anon.websocket_connect("/api/runs/bare/ws") as ws:
            ws.receive_json()
    assert anon.get("/api/runs", headers={"authorization": "Bearer s3cret-token"}).status_code == 200
    browser = TestClient(app)
    r = browser.get("/?token=s3cret-token", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert "httponly" in r.headers["set-cookie"].lower()
    assert browser.get("/api/runs").status_code == 200  # cookie from now on
    with browser.websocket_connect("/api/runs/bare/ws") as ws:
        assert ws.receive_json()["type"] == "pending"
