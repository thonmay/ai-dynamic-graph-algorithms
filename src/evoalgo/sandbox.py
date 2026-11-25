# AI-assisted code: generated and revised with GLM-5.2, Claude Opus 5.5, DeepSeek-V4-Flash and Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Sandbox: isolated execution of candidate code.

Candidate code is untrusted (LLM-written). It runs in a subprocess inside a
Linux namespace jail (see _jail_argv): no network, its own pid namespace, and a
read-only file tree holding only the interpreter and its import paths, so it
cannot reach the user's files, credentials, or the verifier's environment.
Resource limits (address space, CPU time, processes; see _limits), capped
stdout/stderr and a wall-clock timeout keep it from exhausting the host. It
sees only adjacency matrices and edge tuples, never the verifier, test graphs
or oracle. Where the jail is unavailable the sandbox refuses to run unless
EVOALGO_SANDBOX=none is set.

All test cases of a chunk go to one subprocess, which avoids ~160 ms of Python
start-up per case (thousands of graphs at n >= 4).
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import shutil
import sys
import textwrap
from pathlib import Path
from typing import Any


# -- jail ---------------------------------------------------------------------
#
# Candidate code is LLM-written and runs as the user, so an environment scrub
# alone is not enough: it could read /proc/<ppid>/environ (the verifier holds
# the user's API keys), token files such as ~/.netrc, open sockets, or
# patch the verifier. The jail uses unprivileged user namespaces only (no
# root, no extra packages):
#
#   unshare -rnmpfi   new user (mapped to root inside), net (loopback only,
#                     down), mount, pid and IPC namespaces (SysV shared
#                     memory would otherwise outlive the candidate on the host)
#   mount script      bind the host tree at /mnt, hide /home, /proj, /tmp,
#                     /var, /local, /repo and the run/session dirs behind tmpfs,
#                     bind back only the interpreter's import paths, make the
#                     whole tree read-only (mount_setattr AT_RECURSIVE),
#                     fresh /proc and /tmp, pivot_root into it
#   unshare -U        a second user namespace mapped back to the real uid, so
#                     the candidate keeps no capabilities over its mounts
#
# The candidate source travels in the JSON input, not as a path, so the run
# directory is never visible inside.

JAIL_ENV = "EVOALGO_SANDBOX"  # "none" disables the jail (not recommended)
# Host directories hidden behind an empty tmpfs: user data, shared NFS, temp,
# and /run (host daemon sockets: nscd answers DNS, dbus, systemd; a unix
# socket can be connected on a read-only mount, so it must not be visible).
# /var (system logs, caches, package state), /opt, /boot and /etc/ssh hold
# host data a candidate could copy into its result, which reaches the LLM.
# /etc itself stays: the interpreter needs ld.so.cache, locale and passwd
# lookups; what remains there is world-readable host configuration.
HIDDEN_DIRS = ("/home", "/proj", "/tmp", "/var", "/local", "/repo", "/root",
               "/run", "/dev/shm", "/net", "/mnt", "/media", "/srv", "/afs",
               "/opt", "/boot", "/workspace", "/etc/ssh")

_JAIL_SCRIPT = r'''
set -e
uid=$1; gid=$2; r=$3; shift 3
mount --rbind / "$r"
while [ "$1" != "--keep" ]; do
  # Not through a symlink: it would resolve against the host root.
  if [ -d "$r$1" ] && [ ! -L "$r$1" ]; then mount -t tmpfs -o size=1m,mode=755 none "$r$1"; fi
  shift
done
shift
while [ "$1" != "--" ]; do
  mkdir -p "$r$1"
  mount --rbind "$1" "$r$1"
  shift
done
shift
"$1" -I -S -c "$_EVOALGO_RDONLY" "$r"
mount -t tmpfs -o size=64m,mode=1777 none "$r/tmp"
mount -t proc proc "$r/proc"
cd "$r"
mkdir tmp/.old
pivot_root . tmp/.old
umount -l /tmp/.old
rmdir /tmp/.old
cd /
# This shell stays pid 1 and waits, so the runner is not pid 1 (pid 1 ignores
# signals it has no handler for), and it names the signal that ended the
# runner: unshare --fork's own report of that differs between util-linux
# versions. Its credentials are of this namespace: the runner cannot read it.
r=0
unshare -U --map-user="$uid" --map-group="$gid" -- "$@" || r=$?
if [ "$r" -gt 128 ]; then echo "EVOALGO_SIGNAL $((r - 128))" >&2; fi
exit "$r"
'''

# Recursive read-only remount. util-linux's ro=recursive does not apply to
# submounts on every version; mount_setattr(2) with AT_RECURSIVE does.
_RDONLY_SRC = r'''
import ctypes, os, sys
class A(ctypes.Structure):
    _fields_ = [("set", ctypes.c_uint64), ("clr", ctypes.c_uint64),
                ("prop", ctypes.c_uint64), ("userns", ctypes.c_uint64)]
libc = ctypes.CDLL(None, use_errno=True)
a = A(1, 0, 0, 0)  # MOUNT_ATTR_RDONLY
if libc.syscall(442, -100, sys.argv[1].encode(), 0x8000, ctypes.byref(a), ctypes.sizeof(a)):
    sys.exit("mount_setattr: " + os.strerror(ctypes.get_errno()))
'''


def _under(path: str, roots: list[str] | tuple[str, ...]) -> bool:
    return any(path == r or path.startswith(r.rstrip("/") + "/") for r in roots)


def _keep_paths(python: str) -> list[str]:
    """Hidden directories the interpreter needs back: its prefixes (venv and
    base install). Import-path entries outside them (an editable install's
    source tree, user site) stay hidden; the runner only needs numpy."""
    probe = ("import json, sys; print(json.dumps([sys.prefix, sys.base_prefix, "
             "sys.exec_prefix, sys.base_exec_prefix]))")
    out = subprocess.run([python, "-I", "-c", probe], capture_output=True, text=True,
                         timeout=30, env={"PATH": "/usr/bin:/bin"}, check=True).stdout
    paths: set[str] = set()
    for p in json.loads(out):
        for candidate in (os.path.normpath(p), os.path.realpath(p)):
            if os.path.isdir(candidate) and _under(candidate, HIDDEN_DIRS):
                paths.add(candidate)
    kept: list[str] = []
    for p in sorted(paths):  # parents sort first; skip what a parent covers
        if not _under(p, kept):
            kept.append(p)
    return kept


_JAIL_CACHE: dict[tuple[str, tuple[str, ...]], list[str]] = {}


def _jail_prefix(python: str, readonly: tuple[str, ...] = ()) -> list[str] | None:
    """argv prefix that runs ``python`` in the jail, or None when disabled.

    ``readonly``: extra host directories to expose read-only (trusted code
    such as the repo's ``src`` for a script that imports evoalgo; never a
    directory holding credentials).

    Raises RuntimeError if the jail is wanted but does not work here: failing
    closed, since running candidates unconfined exposes the user's secrets.
    """
    if os.environ.get(JAIL_ENV) == "none":
        return None
    # Lexically, not realpath: a venv's python is a symlink that must stay
    # inside the venv. A ".." would walk through directories the jail hides.
    python = os.path.abspath(python)
    key = (python, tuple(sorted(os.path.realpath(p) for p in readonly)))
    if key not in _JAIL_CACHE:
        hint = f"set {JAIL_ENV}=none to run candidates unconfined at your own risk"
        if not sys.platform.startswith("linux") or not shutil.which("unshare"):
            raise RuntimeError(f"the sandbox needs Linux user namespaces (unshare); {hint}")
        try:
            keep = sorted(set(_keep_paths(python)) | set(key[1]))
            keep = [p for i, p in enumerate(keep) if not _under(p, keep[:i])]
            prefix = _jail_argv(python, keep)
            probe = subprocess.run(prefix + ["-I", "-c", "import numpy; print('ok')"],
                                   capture_output=True, text=True, timeout=60, env=_jail_env())
        except (OSError, subprocess.SubprocessError) as e:
            raise RuntimeError(f"the sandbox jail does not start ({type(e).__name__}); {hint}") from e
        if probe.stdout.strip() != "ok":
            raise RuntimeError(f"the sandbox jail does not start "
                               f"({(probe.stderr or '').strip()[-300:]}); {hint}")
        _JAIL_CACHE[key] = prefix
    return _JAIL_CACHE[key]


def jailed_python(readonly: tuple[str, ...] = (), python: str | None = None) -> tuple[list[str], dict[str, str]]:
    """(argv prefix, env) to run untrusted code with this interpreter in the
    jail, for scripts outside the verifier (benchmarks, cross-checks).
    Append ``["-I", "-B", "-c", source, ...]`` or a script path inside
    ``readonly``."""
    python = python or sys.executable
    prefix = _jail_prefix(python, readonly)
    if prefix is None:
        return [python], {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent"}
    return prefix, _jail_env()


def _jail_argv(python: str, keep: list[str]) -> list[str]:
    hidden = sorted({d for h in HIDDEN_DIRS for d in (h, os.path.realpath(h))})
    return ["unshare", "-rnmpfi", "--kill-child", "sh", "-c", _JAIL_SCRIPT, "jail",
            str(os.getuid()), str(os.getgid()), _staging_dir(), *hidden, "--keep", *keep,
            "--", python]


def _staging_dir() -> str:
    """Where the jail assembles its tree: an existing directory, since an
    unprivileged user cannot create one at the host root. /tmp always exists."""
    return "/mnt" if os.path.isdir("/mnt") and not os.path.islink("/mnt") else "/tmp"


# numpy's BLAS otherwise starts one thread per core in every runner: the
# candidate needs none, and threads count against the process limit.
_THREAD_ENV = {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def _jail_env() -> dict[str, str]:
    return {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "HOME": "/nonexistent", "LANG": "C.UTF-8",
            "_EVOALGO_RDONLY": _RDONLY_SRC, **_THREAD_ENV}


# -- resource limits ----------------------------------------------------------
#
# The jail stops a candidate reading or writing the host; these stop it
# exhausting it. Set by the runner before candidate code runs, soft = hard, so
# the candidate cannot raise them (raising a hard limit needs CAP_SYS_RESOURCE
# in the initial user namespace). RLIMIT_NPROC counts per user namespace, and
# every runner has its own, so parallel workers do not share the budget.
# Measured: a final-grade chunk (1000 base graphs at n = 5) peaks near 620 MB
# resident and returns about 50 MB of JSON.
MEMORY_LIMIT_MB = 4096      # address space per runner
MAX_FILE_MB = 16            # largest file, also memory files (memfd); /tmp is 64 MB
MAX_OPEN_FILES = 64         # file descriptors (numpy's import needs about 10)
MAX_PROCESSES = 4           # tasks of the uid in the runner's user namespace
                            # (inner unshare + runner + 2 for the candidate)
MAX_RESULT_MB = 256         # result JSON the verifier will read
MAX_STDERR_KB = 64          # stderr tail kept for error messages
CPU_GRACE_SECONDS = 5       # CPU limit = wall-clock timeout + this


def _limits(timeout: float, jailed: bool) -> dict[str, int]:
    """rlimits the runner applies to itself. Without the jail the process
    limit would count every process of the user on the host, so it is left
    out (EVOALGO_SANDBOX=none is unconfined anyway)."""
    limits = {"RLIMIT_AS": MEMORY_LIMIT_MB << 20,
              "RLIMIT_CPU": int(timeout) + CPU_GRACE_SECONDS,
              # Also bounds memfd_create files, which RLIMIT_AS does not
              # count; with the open-file limit, memory files total at most
              # MAX_OPEN_FILES * MAX_FILE_MB.
              "RLIMIT_FSIZE": MAX_FILE_MB << 20,
              "RLIMIT_NOFILE": MAX_OPEN_FILES,
              "RLIMIT_CORE": 0}
    if jailed:
        limits["RLIMIT_NPROC"] = MAX_PROCESSES
    return limits


def _read_capped(stream, cap: int, keep_tail: bool, out: dict) -> None:
    """Drain ``stream``; keep at most ``cap`` bytes (the head, or the tail when
    ``keep_tail``). Sets out["overflow"] when more arrived."""
    buf = bytearray()
    while chunk := stream.read(1 << 16):
        buf += chunk
        if len(buf) > cap:
            out["overflow"] = True
            if keep_tail:
                del buf[:-cap]
            else:
                del buf[cap:]
                if out.get("kill"):
                    out["kill"]()
                    break
    out["data"] = bytes(buf)


def _run_capped(argv: list[str], input_bytes: bytes, env: dict[str, str], timeout: float,
                stdout_cap: int, stderr_cap: int):
    """subprocess.run with bounded memory: stdout beyond ``stdout_cap`` kills
    the process, stderr keeps its last ``stderr_cap`` bytes.

    Returns (returncode, stdout, stderr, timed_out, stdout_overflow).
    """
    import threading

    # Own process group: unjailed (EVOALGO_SANDBOX=none), a forked child of
    # the candidate would keep the pipes open after the runner is killed.
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env, start_new_session=True)

    def kill():
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    out: dict = {"kill": kill}
    err: dict = {}

    def feed():
        try:
            proc.stdin.write(input_bytes)
        except (BrokenPipeError, OSError):
            pass  # the runner died before reading all input
        finally:
            try:
                proc.stdin.close()
            except OSError:
                pass

    threads = [threading.Thread(target=feed, daemon=True),
               threading.Thread(target=_read_capped, args=(proc.stdout, stdout_cap, False, out), daemon=True),
               threading.Thread(target=_read_capped, args=(proc.stderr, stderr_cap, True, err), daemon=True)]
    for t in threads:
        t.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
    kill()  # whatever of the group is left (nothing, jailed: --kill-child)
    proc.wait()
    for t in threads:
        t.join()
    return (proc.returncode, out.get("data", b""), err.get("data", b""), timed_out,
            bool(out.get("overflow")))


_RUNNER_TEMPLATE = textwrap.dedent('''
import json, os, sys, time, traceback, copy

# Bound before any candidate code runs, which shares this interpreter: it
# could patch time, json, os or builtins to fake its timing or its output.
# This closes the direct routes only; timing is best-effort against a
# candidate that walks frames or patches json internals (correctness is not
# affected: the verifier re-checks every state it receives).
_dumps, _write, _out = json.dumps, os.write, os.dup(1)

def run():
    data = json.load(sys.stdin)
    module_path = data["module_path"]
    directed = data.get("directed", True)
    offline_src = data.get("offline_src", "")
    root = data.get("root", None)
    test_cases = data["test_cases"]
    repeat = max(1, data.get("repeat", 20))

    clock = time.perf_counter_ns
    reps = tuple(range(repeat))  # no range() call in the timed loops
    np = __import__("numpy")  # before the candidate can patch what it imports
    # Resource limits (see the constants in sandbox.py), with hard limits the
    # candidate cannot raise. After numpy: its import maps more memory.
    import resource, signal
    for name, value in data.get("limits", {}).items():
        # CPU: the kernel sends SIGKILL at the hard limit, SIGXCPU at the
        # soft one; equal limits would skip the signal handled below.
        hard = value + 1 if name == "RLIMIT_CPU" else value
        resource.setrlimit(getattr(resource, name), (value, hard))
    # Through unshare the parent cannot see which signal ended the runner, so
    # say it here. A candidate that replaces the handler is SIGKILLed one CPU
    # second later instead (reported as "killed").
    _err = os.dup(2)
    def _on_xcpu(*_):
        os.write(_err, b"\\nEVOALGO_CPU_LIMIT\\n")
        os._exit(152)
    signal.signal(signal.SIGXCPU, _on_xcpu)
    # The candidate's prints go to stderr, not into the result channel.
    sys.stdout = sys.stderr
    import linecache, types
    src = data["module_src"]
    # The file is not visible in the jail: give tracebacks its lines.
    linecache.cache[module_path] = (len(src), None, src.splitlines(True), module_path)
    mod = types.ModuleType("candidate")
    mod.__file__ = module_path
    sys.modules["candidate"] = mod
    exec(compile(src, module_path, "exec"), mod.__dict__)

    for fn in ("init", "insert_edge", "delete_edge"):
        if not hasattr(mod, fn):
            return {"status": "crash", "error": f"Missing function: {fn}"}

    offline_fn = None
    if offline_src:
        ns = {"np": __import__("numpy")}
        exec(compile(offline_src, "<offline>", "exec"), ns)
        offline_fn = ns.get("offline_compute")

    all_results = []

    try:
        for tc_idx, tc in enumerate(test_cases):
            graph = tc["graph"]
            sequences = tc["sequences"]
            graph_results = []

            for seq_idx, seq in enumerate(sequences):
                ops = seq  # list of {type, edge}
                current_graph = [row[:] for row in graph]
                results = []
                timings = []
                offline_timings = []

                try:
                    # Init. Each repeat gets its own graph copy (made outside
                    # the timed region) so a cache keyed on the graph object
                    # cannot turn the repeats into lookups.
                    graph_copies = [[row[:] for row in current_graph] for _ in reps]
                    t0 = clock()
                    for i in reps:
                        _ = mod.init(graph_copies[i])
                    t1 = clock()
                    timings.append((t1 - t0) // repeat // 1000)
                    state = mod.init(current_graph)
                    results.append({"after": "init", "state": _serialize(state)})

                    if offline_fn:
                        g_np = np.array(current_graph)
                        t0 = clock()
                        for _ in reps:
                            offline_fn(g_np, root)
                        t1 = clock()
                        offline_timings.append((t1 - t0) // repeat // 1000)

                    for op in ops:
                        op_type = op["type"]
                        edge = tuple(op["edge"])
                        u, v = edge
                        if op_type == "insert":
                            current_graph[u][v] = 1
                            if not directed:
                                current_graph[v][u] = 1
                            fn = mod.insert_edge
                        elif op_type == "delete":
                            current_graph[u][v] = 0
                            if not directed:
                                current_graph[v][u] = 0
                            fn = mod.delete_edge
                        else:
                            raise ValueError(f"Unknown op: {op_type}")

                        pre_state = copy.deepcopy(state)
                        # Pre-allocate copies so deepcopy overhead is
                        # outside the timed region
                        state_copies = [copy.deepcopy(pre_state) for _ in reps]
                        graph_copies = [[row[:] for row in current_graph] for _ in reps]
                        t0 = clock()
                        for i in reps:
                            _ = fn(graph_copies[i], edge, state_copies[i])
                        t1 = clock()
                        timings.append((t1 - t0) // repeat // 1000)
                        state = fn(current_graph, edge, state)

                        if offline_fn:
                            g_np = np.array(current_graph)
                            t0 = clock()
                            for _ in reps:
                                offline_fn(g_np, root)
                            t1 = clock()
                            offline_timings.append((t1 - t0) // repeat // 1000)

                        results.append({"after": op_type + " " + str(edge),
                                        "state": _serialize(state)})

                    graph_results.append({
                        "status": "ok",
                        "results": results,
                        "timings": timings,
                        "offline_timings": offline_timings,
                    })
                except Exception as e:
                    graph_results.append({
                        "status": "crash",
                        "error": _describe(e, module_path),
                        "traceback": traceback.format_exc(),
                        "partial_results": results,
                        "partial_timings": timings,
                        "partial_offline_timings": offline_timings,
                    })

            all_results.append(graph_results)

        return {"status": "ok", "all_results": all_results}
    except Exception as e:
        return {"status": "crash", "error": _describe(e, module_path),
                "traceback": traceback.format_exc(),
                "partial_all_results": all_results}

def _describe(e, module_path=None):
    """Type, message and the candidate's failing line: str(KeyError(0)) is just '0'."""
    try:
        where = ""
        for fs in reversed(traceback.extract_tb(e.__traceback__)):
            if module_path and fs.filename == module_path:
                where = " at line %d: %s" % (fs.lineno, (fs.line or "").strip())
                break
        return "%s: %s%s" % (type(e).__name__, e, where)
    except Exception:
        return type(e).__name__

def _serialize(obj):
    import numpy as np
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(x) for x in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj

result = run()
data = (_dumps(result) + "\\n").encode()
while data:
    data = data[_write(_out, data):]
''').strip()


class SandboxResult:
    """Result of executing a candidate in the sandbox."""

    def __init__(
        self,
        status: str,  # "ok", "crash", "timeout"
        all_results: list[list[dict]] | None = None,
        error: str | None = None,
        traceback_str: str | None = None,
    ):
        self.status = status
        self.all_results = all_results
        self.error = error
        self.traceback_str = traceback_str

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"

    @property
    def is_crash(self) -> bool:
        return self.status == "crash"

    @property
    def is_timeout(self) -> bool:
        return self.status == "timeout"


class Sandbox:
    """Executes candidate code in an isolated subprocess."""

    def __init__(self, timeout_seconds: int = 30, python_path: str | None = None,
                 directed: bool = True):
        self.timeout = timeout_seconds
        self.python = python_path or sys.executable
        self.directed = directed

    def execute_batch(
        self,
        module_path: Path | str,
        test_cases: list[dict[str, Any]],
        offline_src: str | None = None,
        root: int | None = None,
        repeat: int = 20,
        timeout: int | None = None,
    ) -> SandboxResult:
        """Run a candidate on all test cases in one subprocess.

        ``test_cases`` is a list of {graph, sequences}, each sequence a list of
        {type: insert|delete, edge: [u, v]}. ``repeat`` amplifies the timing;
        ``timeout`` (default ``self.timeout``) is per call, so the verifier can give
        each chunk its own limit. The result's ``all_results`` holds, per graph and
        sequence, a dict with status, results, timings and offline_timings (or a crash
        with error, traceback and partial results).
        """
        module_path = Path(module_path)
        call_timeout = self.timeout if timeout is None else timeout

        jail = _jail_prefix(self.python)  # outside the try: a jail failure is not the candidate's
        input_data = {
            "module_path": str(module_path),  # only for tracebacks; the source is sent
            "module_src": module_path.read_text(),
            "directed": self.directed,
            "offline_src": offline_src or "",
            "root": root,
            "test_cases": test_cases,
            "repeat": repeat,
            "limits": _limits(call_timeout, jailed=jail is not None),
        }

        argv = (jail or [self.python]) + ["-I", "-B", "-c", _RUNNER_TEMPLATE]
        rc, out, err, timed_out, overflow = _run_capped(
            argv, json.dumps(input_data).encode(),
            env=_jail_env() if jail else {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", **_THREAD_ENV},
            timeout=call_timeout, stdout_cap=MAX_RESULT_MB << 20, stderr_cap=MAX_STDERR_KB << 10)
        stdout = out.decode(errors="replace")
        stderr = err.decode(errors="replace")

        if timed_out:
            return SandboxResult(status="timeout", error=f"Exceeded {call_timeout}s")
        if overflow:
            return SandboxResult(status="crash", error=f"Output exceeded {MAX_RESULT_MB} MB")

        if "EVOALGO_CPU_LIMIT" in stderr[-200:]:
            return SandboxResult(status="timeout", error="CPU time limit exceeded")
        # Jailed, the reaper reports the signal; unjailed, the return code is -N.
        signalled = jail and f"EVOALGO_SIGNAL {int(signal.SIGKILL)}" in stderr[-200:]
        if rc == -signal.SIGKILL or signalled:
            return SandboxResult(status="timeout", error="Process killed (OOM or CPU limit)")

        if rc != 0 and not stdout:
            return SandboxResult(status="crash", error=stderr or f"Exit code {rc}")

        try:
            result = json.loads(stdout)
        except (ValueError, RecursionError):  # JSONDecodeError, or nesting a candidate forged
            return SandboxResult(
                status="crash",
                error=f"Invalid output from runner: {stdout[:500]}",
                traceback_str=stderr,
            )

        if result.get("status") == "ok":
            return SandboxResult(
                status="ok",
                all_results=result.get("all_results", []),
            )
        elif result.get("status") == "crash":
            return SandboxResult(
                status="crash",
                error=result.get("error"),
                traceback_str=result.get("traceback"),
                all_results=result.get("partial_all_results"),
            )
        else:
            return SandboxResult(
                status="crash",
                error=f"Unknown status: {result.get('status')}",
            )


