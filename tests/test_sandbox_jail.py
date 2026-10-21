"""The sandbox jail: untrusted candidate code cannot reach secrets or the network."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from evoalgo import sandbox
from evoalgo.sandbox import Sandbox

pytestmark = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux namespaces")

PROBE = '''
import os, socket
def _probe():
    out = {}
    try:
        open(f"/proc/{os.getppid()}/environ", "rb").read(); out["ppid_environ"] = "read"
    except OSError:
        out["ppid_environ"] = "blocked"
    out["leaky_procs"] = 0
    for pid in filter(str.isdigit, os.listdir("/proc")):
        try:
            out["leaky_procs"] += b"EVOALGO_TEST_SECRET" in open(f"/proc/{pid}/environ", "rb").read()
        except OSError:
            pass
    out["env"] = "EVOALGO_TEST_SECRET" in os.environ
    out["secret_file"] = os.path.exists(SECRET_FILE)
    out["repo"] = os.path.exists(REPO_FILE)
    try:
        open(VENV_FILE, "w"); out["venv_write"] = "ok"
    except OSError:
        out["venv_write"] = "blocked"
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=2); out["net"] = "open"
    except OSError:
        out["net"] = "blocked"
    try:  # DNS through the host's nscd socket would leak data without a network
        socket.gethostbyname("localhost.localdomain.example"); out["dns"] = "open"
    except OSError:
        out["dns"] = "blocked"
    out["run_sockets"] = [n for n in ("/run/dbus/system_bus_socket", "/run/nscd/socket",
                                      "/run/systemd/journal/socket") if os.path.exists(n)]
    out["pid1"] = os.getpid() == 1
    return out
def init(graph): return {"probe": _probe()}
def insert_edge(graph, edge, state): return state
def delete_edge(graph, edge, state): return state
'''


def test_candidate_cannot_reach_secrets_or_network(tmp_path, monkeypatch):
    if os.environ.get(sandbox.JAIL_ENV) == "none":
        pytest.skip("jail disabled")
    home_secret = Path.home() / ".evoalgo_jail_test_secret"
    home_secret.write_text("x")
    try:
        monkeypatch.setenv("EVOALGO_TEST_SECRET", "x")  # the verifier's env, like an API key
        cand = tmp_path / "cand.py"
        cand.write_text(f"SECRET_FILE = {str(home_secret)!r}\n"
                        f"REPO_FILE = {str(Path(sandbox.__file__))!r}\n"
                        f"VENV_FILE = {str(Path(sys.prefix) / 'jail_test_write')!r}\n" + PROBE)
        r = Sandbox(timeout_seconds=60).execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}],
                                                       repeat=1)
        assert r.is_ok, (r.error, r.traceback_str)
        probe = r.all_results[0][0]["results"][0]["state"]["probe"]
        assert probe == {"ppid_environ": "blocked", "leaky_procs": 0, "env": False,
                         "secret_file": False, "repo": False, "venv_write": "blocked",
                         "net": "blocked", "dns": "blocked", "run_sockets": [], "pid1": False}
    finally:
        home_secret.unlink()
        (Path(sys.prefix) / "jail_test_write").unlink(missing_ok=True)


def test_jail_fails_closed(monkeypatch):
    monkeypatch.delenv(sandbox.JAIL_ENV, raising=False)
    monkeypatch.setattr(sandbox, "_JAIL_CACHE", {})
    monkeypatch.setattr(sandbox.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError, match="EVOALGO_SANDBOX=none"):
        sandbox._jail_prefix(sys.executable)


def test_killed_candidate_is_reported_as_kill_and_traceback_has_line(tmp_path):
    cand = tmp_path / "cand.py"
    cand.write_text("import os, signal\n"
                    "def init(graph):\n"
                    "    if graph == [[0]]:\n"
                    "        os.kill(os.getpid(), signal.SIGKILL)\n"
                    "    return {}[0]\n"
                    "def insert_edge(graph, edge, state): return state\n"
                    "def delete_edge(graph, edge, state): return state\n")
    sb = Sandbox(timeout_seconds=60)
    killed = sb.execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}], repeat=1)
    assert killed.status == "timeout" and "killed" in killed.error
    err = sb.execute_batch(cand, [{"graph": [[0, 0], [0, 0]], "sequences": [[]]}], repeat=1)
    assert err.all_results[0][0]["error"] == "KeyError: 0 at line 5: return {}[0]"
