"""Tests for the web UI server (HTTP API, websocket stream, control)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from evoalgo import server  # noqa: E402
from evoalgo.events import CONTROL_FILE, EventLog, backfill  # noqa: E402

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


def test_websocket_backlog_from_offset_and_live(client, runs):
    with client.websocket_connect("/api/runs/mcs_pressure_e2e/ws?from=20") as ws:
        first = ws.receive_json()
        assert first["seq"] == 20
        rest = [ws.receive_json() for _ in range(5)]
        assert rest[-1]["type"] == "run_end"
        EventLog(runs / "mcs_pressure_e2e").emit("note", text="live")
        live = ws.receive_json()
        assert live["type"] == "note" and live["seq"] == 26


def test_websocket_control(client, runs):
    with client.websocket_connect("/api/runs/bare/ws") as ws:
        ws.send_json({"cmd": "set", "field": "population_size", "value": 0})
        assert ws.receive_json()["type"] == "error"
        ws.send_text("not json")
        assert ws.receive_json()["type"] == "error"
        ws.send_json({"cmd": "hint", "text": "try lazy repair", "extra": "dropped"})
        reply = ws.receive_json()
        assert reply["type"] == "queued" and reply["cmd"] == "hint"
    lines = (runs / "bare" / CONTROL_FILE).read_text().splitlines()
    assert len(lines) == 1 and '"extra"' not in lines[0]


def test_cross_site_origin_refused(client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/runs/bare/ws",
                                      headers={"origin": "https://evil.example"}) as ws:
            ws.receive_json()
    r = client.post("/api/runs", json={"config": "bare/config.yaml"},
                    headers={"origin": "https://evil.example"})
    assert r.status_code == 403


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
                    headers={"origin": "http://127.0.0.1:8765"})
    assert r.status_code == 201 and r.json()["run_id"] == "new_run"
    cmd = calls[0]
    assert cmd[-2:] == ["--run-id", "new_run"] and cmd[2] == "evoalgo.cli"
    saved = (runs / ".launch" / "new_run.yaml").read_text()
    assert "max_generations: 2" in saved
    assert all(r["run_id"] != ".launch" for r in client.get("/api/runs").json())
