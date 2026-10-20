"""Sandbox: isolated execution of candidate code.

Executes candidate algorithms in a subprocess with:
  - wall-clock timeout
  - restricted environment (no PATH pollution)
  - stdout/stderr capture
  - structured result output

The candidate module is imported and its init/insert_edge/delete_edge are
called in the subprocess. The result (state or exception) is returned
as a structured record via JSON over stdout.

Trust boundary: candidate code never sees the verifier, test graphs, or
oracle. It only receives adjacency matrices and edge tuples.

Batched execution: all test cases for a candidate are sent to a single
subprocess. This avoids paying ~160ms Python startup cost per test case,
which makes the system unworkable at n>=4 where exhaustive digraph
enumeration produces thousands of graphs.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import traceback
from pathlib import Path
from typing import Any

import numpy as np

# Runner script that executes inside the subprocess
def _runner_file() -> str:
    """The runner script, written once per process and content (not per call).

    A per-call temp file was left behind whenever the parent was killed
    (timeouts, Ctrl-C), hundreds per run. One file per process and template
    version, overwritten atomically, leaves at most one.
    """
    import hashlib
    digest = hashlib.sha256(_RUNNER_TEMPLATE.encode()).hexdigest()[:12]
    path = Path(tempfile.gettempdir()) / f"evoalgo_runner_{os.getuid()}_{digest}.py"
    if not path.is_file() or path.read_text() != _RUNNER_TEMPLATE:
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        tmp.write_text(_RUNNER_TEMPLATE)
        os.replace(tmp, path)
    return str(path)


_RUNNER_TEMPLATE = textwrap.dedent('''
import json, sys, time, traceback, copy

def run():
    data = json.load(sys.stdin)
    module_path = data["module_path"]
    directed = data.get("directed", True)
    offline_src = data.get("offline_src", "")
    root = data.get("root", None)
    test_cases = data["test_cases"]
    repeat = max(1, data.get("repeat", 20))

    import importlib.util
    spec = importlib.util.spec_from_file_location("candidate", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    for fn in ("init", "insert_edge", "delete_edge"):
        if not hasattr(mod, fn):
            return {"status": "crash", "error": f"Missing function: {fn}"}

    offline_fn = None
    if offline_src:
        ns = {"np": __import__("numpy")}
        exec(compile(offline_src, "<offline>", "exec"), ns)
        offline_fn = ns.get("offline_compute")

    np = __import__("numpy")
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
                    # Init
                    t0 = time.perf_counter_ns()
                    for _ in range(repeat):
                        _ = mod.init(current_graph)
                    t1 = time.perf_counter_ns()
                    timings.append((t1 - t0) // repeat // 1000)
                    state = mod.init(current_graph)
                    results.append({"after": "init", "state": _serialize(state)})

                    if offline_fn:
                        g_np = np.array(current_graph)
                        t0 = time.perf_counter_ns()
                        for _ in range(repeat):
                            offline_fn(g_np, root)
                        t1 = time.perf_counter_ns()
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
                        state_copies = [copy.deepcopy(pre_state) for _ in range(repeat)]
                        t0 = time.perf_counter_ns()
                        for i in range(repeat):
                            _ = fn(current_graph, edge, state_copies[i])
                        t1 = time.perf_counter_ns()
                        timings.append((t1 - t0) // repeat // 1000)
                        state = fn(current_graph, edge, state)

                        if offline_fn:
                            g_np = np.array(current_graph)
                            t0 = time.perf_counter_ns()
                            for _ in range(repeat):
                                offline_fn(g_np, root)
                            t1 = time.perf_counter_ns()
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

if __name__ == "__main__":
    result = run()
    json.dump(result, sys.stdout)
    sys.stdout.write("\\n")
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
        """Run a candidate against all test cases in a single subprocess.

        Args:
            module_path: path to the candidate .py file
            test_cases: list of {graph: list[list[int]], sequences: list[list[dict]]}
                        where each sequence is a list of {type: insert|delete, edge: [u, v]}
            offline_src: source of the offline_compute baseline function
            root: root/source vertex for problems that need one
            repeat: REPEAT amplification for timing (fewer for large test sets)
            timeout: per-call wall-clock seconds. Defaults to ``self.timeout``.
                The verifier passes a per-chunk timeout so a candidate that
                loops forever on one chunk still fails fast, while the whole
                batch is split across several subprocesses.

        Returns:
            SandboxResult with all_results: list[per_graph: list[per_seq: dict]]
            Each per-seq dict has: status, results, timings, offline_timings
            (or status=crash with error/traceback + partial results)
        """
        module_path = Path(module_path)
        call_timeout = self.timeout if timeout is None else timeout

        runner_path = _runner_file()

        input_data = {
            "module_path": str(module_path),
            "directed": self.directed,
            "offline_src": offline_src or "",
            "root": root,
            "test_cases": test_cases,
            "repeat": repeat,
        }

        try:
            proc = subprocess.run(
                [self.python, runner_path],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=call_timeout,
                env={
                    "HOME": os.environ.get("HOME", "/tmp"),
                    "PATH": "/usr/bin:/bin",
                    "PYTHONPATH": "",
                },
            )

            if proc.returncode == -signal.SIGKILL or proc.returncode == 137:
                return SandboxResult(status="timeout", error="Process killed (likely OOM)")

            if proc.returncode != 0 and not proc.stdout:
                return SandboxResult(
                    status="crash",
                    error=proc.stderr or f"Exit code {proc.returncode}",
                )

            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                return SandboxResult(
                    status="crash",
                    error=f"Invalid output from runner: {proc.stdout[:500]}",
                    traceback_str=proc.stderr,
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

        except subprocess.TimeoutExpired:
            return SandboxResult(status="timeout", error=f"Exceeded {call_timeout}s")

    def execute(
        self,
        module_path: Path | str,
        graph: np.ndarray,
        operations: list[dict[str, Any]],
        offline_src: str | None = None,
        root: int | None = None,
    ) -> SandboxResult:
        """Run a candidate module on a single graph with a sequence of operations.

        Legacy single-test interface. Returns a SandboxResult with
        all_results containing a single graph with a single sequence.
        """
        test_cases = [{
            "graph": graph.tolist() if isinstance(graph, np.ndarray) else graph,
            "sequences": [operations],
        }]
        batch_result = self.execute_batch(module_path, test_cases, offline_src, root)
        # Flatten: all_results[0][0] is the single sequence result
        if batch_result.is_ok and batch_result.all_results:
            seq_result = batch_result.all_results[0][0] if batch_result.all_results[0] else None
            if seq_result:
                return _LegacySandboxResult(
                    status=seq_result.get("status", "crash"),
                    results=seq_result.get("results"),
                    timings=seq_result.get("timings"),
                    offline_timings=seq_result.get("offline_timings"),
                    error=seq_result.get("error"),
                    traceback_str=seq_result.get("traceback"),
                )
        return _LegacySandboxResult(
            status=batch_result.status,
            error=batch_result.error,
            traceback_str=batch_result.traceback_str,
        )

    def execute_single(
        self,
        module_path: Path | str,
        graph: np.ndarray,
    ) -> SandboxResult:
        """Execute just init() on a graph and return the initial state."""
        return self.execute(module_path, graph, [])


class _LegacySandboxResult(SandboxResult):
    """Backward-compatible result for the single-test execute() method.

    Inherits is_ok/is_crash/is_timeout from SandboxResult.
    """

    def __init__(
        self,
        status: str,
        results: list[dict] | None = None,
        timings: list[int] | None = None,
        offline_timings: list[int] | None = None,
        error: str | None = None,
        traceback_str: str | None = None,
    ):
        super().__init__(status=status, error=error, traceback_str=traceback_str)
        self.results = results
        self.timings = timings
        self.offline_timings = offline_timings
