# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""The sandbox jail: untrusted candidate code cannot reach secrets or the
network, or exhaust the host's processes, memory, CPU, disk or output."""

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
    # Host data the candidate could copy into its result (which the LLM sees).
    out["host_data"] = [d for d in ("/var/log", "/var/lib", "/opt", "/boot", "/etc/ssh")
                        if os.path.isdir(d) and os.listdir(d)]
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
                         "net": "blocked", "dns": "blocked", "run_sockets": [], "pid1": False,
                         "host_data": []}
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


STUBS = ("def init(graph): return {}\n"
         "def insert_edge(graph, edge, state): return state\n"
         "def delete_edge(graph, edge, state): return state\n")

EXHAUST = {
    "fork": ("import os, time\nfor _ in range(50):\n    if os.fork() == 0:\n"
             "        time.sleep(30); os._exit(0)\n", "crash", "BlockingIOError"),
    "threads": ("import threading, time\nfor _ in range(50):\n"
                "    threading.Thread(target=time.sleep, args=(30,), daemon=True).start()\n",
                "crash", "can't start new thread"),
    "memory": ("x = []\nwhile True:\n    x.append(bytearray(256 << 20))\n", "crash", "MemoryError"),
    "raise_limit": ("import resource\nresource.setrlimit(resource.RLIMIT_AS, "
                    "(resource.RLIM_INFINITY, resource.RLIM_INFINITY))\n",
                    "crash", "not allowed to raise maximum limit"),
    "disk": ("open('/tmp/big', 'wb').write(b'z' * (200 << 20))\n", "crash", "File too large"),
    "disk_many": ("for i in range(20):\n    open(f'/tmp/f{i}', 'wb').write(b'z' * (15 << 20))\n",
                  "crash", "No space left"),
    "stdout_flood": ("import os\nwhile True:\n    os.write(1, b'x' * (1 << 20))\n",
                     "crash", "Output exceeded"),
    # Memory files are outside RLIMIT_AS; file size and fd limits bound them.
    "memfd": ("import os, ctypes\nlibc = ctypes.CDLL(None)\nn = 0\n"
              "while (fd := libc.syscall(319, b'x', 0)) >= 0:\n"
              "    n += 1\n    os.write(fd, b'z' * (1 << 20))\n"
              "raise SystemExit('memfd stopped after %d files' % n)\n", "crash", "memfd stopped"),
    "deep_json": ("import os\nos.write(1, b'[' * 200000)\nos._exit(0)\n", "crash", "Invalid output"),
}


def test_shared_memory_does_not_outlive_the_candidate(tmp_path):
    """SysV segments live in the jail's own IPC namespace, not the host's."""
    if os.environ.get(sandbox.JAIL_ENV) == "none":
        pytest.skip("jail disabled")
    import subprocess

    def segments():
        return subprocess.run(["ipcs", "-m"], capture_output=True, text=True).stdout.count("\n")

    before = segments()
    cand = tmp_path / "cand.py"
    cand.write_text("import ctypes\nassert ctypes.CDLL(None).shmget(0, 1 << 20, 0o1600) >= 0\n" + STUBS)
    r = Sandbox(timeout_seconds=60).execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}],
                                                   repeat=1)
    assert r.is_ok, r.error
    assert segments() == before


def test_unjailed_forked_child_cannot_hold_the_run_open(tmp_path, monkeypatch):
    """Without the jail, a forked child keeping the pipes open must not
    stretch the timeout: the whole process group is killed."""
    import time
    monkeypatch.setenv(sandbox.JAIL_ENV, "none")
    cand = tmp_path / "cand.py"
    cand.write_text("import os, time\nif os.fork() == 0:\n    time.sleep(30); os._exit(0)\n"
                    "while True: pass\n" + STUBS)
    t = time.monotonic()
    r = Sandbox(timeout_seconds=3).execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}],
                                                  repeat=1)
    assert r.is_timeout and time.monotonic() - t < 10


@pytest.mark.parametrize("kind", sorted(EXHAUST))
def test_candidate_cannot_exhaust_host_resources(tmp_path, kind):
    """Process explosion, memory, disk and output floods fail inside the
    runner, quickly, and cannot lift their own limits."""
    if os.environ.get(sandbox.JAIL_ENV) == "none":
        pytest.skip("jail disabled")
    code, status, message = EXHAUST[kind]
    cand = tmp_path / "cand.py"
    cand.write_text(code + STUBS)
    r = Sandbox(timeout_seconds=60).execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}],
                                                   repeat=1)
    assert r.status == status and message in (r.error or ""), (r.status, r.error)


def test_stderr_flood_is_truncated(tmp_path):
    cand = tmp_path / "cand.py"
    cand.write_text("import sys\nfor _ in range(300):\n    sys.stderr.write('y' * (1 << 20))\n"
                    "raise SystemExit(3)\n" + STUBS)
    r = Sandbox(timeout_seconds=60).execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}],
                                                   repeat=1)
    assert r.is_crash and len(r.error) <= sandbox.MAX_STDERR_KB << 10


@pytest.mark.parametrize("handler", ["default", "ignored"])
def test_cpu_limit_stops_a_spinning_candidate(tmp_path, monkeypatch, handler):
    """CPU time is capped near the wall-clock timeout, also for threads and a
    candidate that ignores SIGXCPU (killed at the hard limit)."""
    if os.environ.get(sandbox.JAIL_ENV) == "none":
        pytest.skip("jail disabled")
    monkeypatch.setattr(sandbox, "CPU_GRACE_SECONDS", -28)  # 30 s timeout -> 2 s CPU
    pre = "import signal\nsignal.signal(signal.SIGXCPU, signal.SIG_IGN)\n" if handler == "ignored" else ""
    cand = tmp_path / "cand.py"
    cand.write_text(pre + "import threading\ndef spin():\n    while True: pass\n"
                    "threading.Thread(target=spin, daemon=True).start()\nspin()\n" + STUBS)
    r = Sandbox(timeout_seconds=30).execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}],
                                                   repeat=1)
    expected = "CPU time limit exceeded" if handler == "default" else "killed"
    assert r.is_timeout and expected in r.error, r.error


def test_limits_leave_room_for_a_final_grade_chunk(tmp_path):
    """A correct candidate on a full final-grade-sized chunk stays within the
    memory, process and output limits (measured peak ~620 MB, 50 MB out)."""
    from evoalgo.config import RunConfig
    from evoalgo.selftest.references import reference_code
    from evoalgo.workspace import _verifier

    v = _verifier("dynamic_dfs", RunConfig(), "final", "mixed")
    cases = [{"graph": g.tolist(),
              "sequences": [[{"type": t, "edge": list(e)} for t, e in s] for s in v.get_sequences(n, g)]}
             for n, g in v.test_graphs[-200:]]
    cand = tmp_path / "ref.py"
    cand.write_text(reference_code("dynamic_dfs"))
    r = Sandbox(timeout_seconds=120).execute_batch(cand, cases, offline_src=v._offline_src(),
                                                    root=0, repeat=1)
    assert r.is_ok, r.error


FAKE_TIMING = """
import builtins, json, time
FAKE = '{"status": "ok", "all_results": []}'
time.perf_counter_ns = lambda: 0
builtins.range = lambda *a: iter([0])
json.dump = lambda obj, f, **k: f.write(FAKE)
json.dumps = lambda obj, **k: FAKE
print("noise on stdout")
_seen = {}
def init(graph):
    if id(graph) in _seen:
        return _seen[id(graph)]
    t = time.monotonic()
    while time.monotonic() - t < 0.002:
        pass
    _seen[id(graph)] = s = {}
    return s
def insert_edge(graph, edge, state): return state
def delete_edge(graph, edge, state): return state
"""


def test_candidate_cannot_fake_or_cache_its_timing(tmp_path):
    """Patching the clock, range or json, printing to stdout, or caching by
    graph object must not make a slow candidate look free or forge output."""
    cand = tmp_path / "cand.py"
    cand.write_text(FAKE_TIMING)
    r = Sandbox(timeout_seconds=60).execute_batch(cand, [{"graph": [[0]], "sequences": [[]]}],
                                                   repeat=5)
    assert r.is_ok, (r.error, r.traceback_str)
    assert r.all_results[0][0]["timings"][0] >= 1500  # microseconds per init
