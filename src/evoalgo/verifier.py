# AI-assisted code: generated and revised with GLM-5.2, DeepSeek-V4-Flash, Qwen3.8-27B and Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Verifier: test candidates against invariants.

Each candidate runs in the sandbox on every base graph of the bounded universe
and every operation sequence; after each update its state is checked against
the problem's invariant. Fitness is the fraction of sequences passing;
work_ratio is candidate_work / offline_work.
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .candidate import Candidate, CandidateState
from .graph_generator import (
    generate_test_graphs,
    generate_operation_sequences,
)
from .problem_definitions import ProblemDefinition
from .sandbox import Sandbox

# Base graphs per sandbox subprocess. 2000 takes ~10-15 s for the slowest
# correct candidates at n <= 5, well under a 30-60 s per-chunk timeout, while an
# infinite loop fails fast. Parallel runs use smaller chunks to balance load.
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_PARALLEL_CHUNK_SIZE = 1000


# Measured at n <= 5 with 8 workers: about 14.5 GB in total, so a worker with
# its sandbox runner needs up to about 2 GB.
WORKER_MEMORY_MB = 2048


def _available_memory_mb() -> int | None:
    """MemAvailable, or the cgroup limit when lower (a container's /proc/meminfo
    shows the host's memory)."""
    found = []
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                found.append(int(line.split()[1]) // 1024)
        limit = Path("/sys/fs/cgroup/memory.max").read_text().strip()
        if limit.isdigit():
            found.append(int(limit) >> 20)
    except (OSError, ValueError):
        pass
    return min(found) if found else None


def _default_workers() -> int:
    """Default worker count: modest on a shared build server (80 cores), and
    no more than the available memory holds."""
    workers = min(8, os.cpu_count() or 1)
    mem = _available_memory_mb()
    if mem is not None:
        workers = min(workers, mem // WORKER_MEMORY_MB)
    return max(1, workers)

logger = logging.getLogger(__name__)


def _exhaustive_flip_sequences(
    n: int,
    graph: np.ndarray,
    directed: bool,
    include_twins: bool = False,
) -> list[list[tuple[str, tuple[int, int]]]]:
    """Deterministic short update sequences: every legal single-edge flip.

    With ``include_twins`` also every length-2 path (flip one edge, then each
    other edge). Twins are O(n^4) per graph and used only on the small labelled
    comparison universe; on the nauty universe the singles already cover every
    single-edge flip.
    """
    pairs = [(u, v) for u in range(n) for v in range(n) if u != v and (directed or u < v)]
    single: list[list[tuple[str, tuple[int, int]]]] = []
    for u, v in pairs:
        if graph[u, v]:
            single.append([("delete", (u, v))])
        else:
            single.append([("insert", (u, v))])
    if not include_twins:
        return single
    # length-2 paths: first flip (u,v), then flip (u',v') in the resulting graph
    twins: list[list[tuple[str, tuple[int, int]]]] = []
    for u, v in pairs:
        flipped = graph.copy()
        if flipped[u, v]:
            flipped[u, v] = 0
            if not directed:
                flipped[v, u] = 0
            first: tuple[str, tuple[int, int]] = ("delete", (u, v))
        else:
            flipped[u, v] = 1
            if not directed:
                flipped[v, u] = 1
            first = ("insert", (u, v))
        for u2, v2 in pairs:
            if (u2, v2) == (u, v):
                continue
            if flipped[u2, v2]:
                twins.append([first, ("delete", (u2, v2))])
            else:
                twins.append([first, ("insert", (u2, v2))])
    return single + twins


@dataclass
class VerifyResult:
    """Result of verifying one candidate."""

    candidate_id: str
    state: CandidateState
    fitness: float = 0.0
    work_ratio: float | None = None
    timeout: bool = False
    tests_passed: int = 0
    tests_total: int = 0
    error_message: str | None = None
    failing_case: dict[str, Any] | None = None


class Verifier:
    """Trusted correctness and efficiency tester."""

    def __init__(
        self,
        problem: ProblemDefinition,
        sandbox: Sandbox,
        bound_n_max: int = 5,
        bound_n_random: int = 20,
        bound_seq_len_max: int = 20,
        bound_seq_count: int = 10,
        bound_seed: int = 1337,
        exhaustive_flip_n_max: int = 5,
        chunk_size: int | None = None,
        use_offline: bool = True,
        universe: str = "nauty",
        relabels_per_class: int = 2,
        workers: int | None = None,
        update_mode: str = "mixed",
    ):
        self.problem = problem
        self.sandbox = sandbox
        if update_mode not in ("mixed", "insert_only", "delete_only"):
            raise ValueError(
                f"update_mode must be 'mixed', 'insert_only', or 'delete_only', "
                f"got {update_mode!r}"
            )
        self.update_mode = update_mode
        self.n_max = bound_n_max
        self.n_random = bound_n_random
        self.seq_len_max = bound_seq_len_max
        self.seq_count = bound_seq_count
        self.seed = bound_seed
        self.exhaustive_flip_n_max = exhaustive_flip_n_max
        # workers=1 runs the serial path.
        self.workers = _default_workers() if workers is None else max(1, workers)
        if chunk_size is not None:
            self.chunk_size = chunk_size
        elif self.workers > 1:
            self.chunk_size = DEFAULT_PARALLEL_CHUNK_SIZE
        else:
            self.chunk_size = DEFAULT_CHUNK_SIZE
        # The offline baseline is only needed for work_ratio; the self-test
        # (known-good / faults / controls) skips it to keep wall time low.
        self.use_offline = use_offline
        self.universe = universe
        self.relabels_per_class = relabels_per_class
        # Exhaustive length-2 flip paths (twins) are O(n^4)/graph and are only
        # affordable on the small labeled comparison universe. The nauty
        # universe already covers every single-edge flip via the singles.
        self.use_twins = (universe == "labeled")

        # Cache test graphs (they don't change between candidates)
        self._test_graphs: list[tuple[int, np.ndarray]] | None = None
        self._test_sequences: dict[int, list[list[tuple[str, tuple[int, int]]]]] = {}
        self._test_counts: dict[int, int] | None = None

    @property
    def test_graphs(self) -> list[tuple[int, np.ndarray]]:
        if self._test_graphs is None:
            self._test_graphs = generate_test_graphs(
                self.n_max, self.n_random, self.seed,
                directed=self.problem.directed,
                universe=self.universe,
                rooted=self.problem.needs_root,
                relabels_per_class=self.relabels_per_class,
            )
            counts: dict[int, int] = {}
            for n, _g in self._test_graphs:
                counts[n] = counts.get(n, 0) + 1
            self._test_counts = counts
            logger.info("Generated %d test graphs (n=2..%d, %s, universe=%s): %s",
                        len(self._test_graphs), self.n_max,
                        "directed" if self.problem.directed else "undirected",
                        self.universe, counts)
        return self._test_graphs

    def test_counts(self) -> dict[int, int]:
        """Number of base test graphs per n (computed lazily with test_graphs)."""
        self.test_graphs
        return self._test_counts or {}

    def get_sequences(self, n: int, graph: np.ndarray) -> list[list[tuple[str, tuple[int, int]]]]:
        key = (n, graph.tobytes())
        if key not in self._test_sequences:
            seqs = generate_operation_sequences(
                n, graph, self.seq_len_max, self.seq_count, self.seed + n,
                directed=self.problem.directed,
            )
            # Deterministic exhaustive single-edge flips for small n (and, on
            # the labeled comparison universe, a compact set of 2-flip paths).
            # Random sequences alone missed reachable counterexamples (e.g. a
            # single insert breaking dynamic MCS at n=3), so close that gap
            # for the sizes where exhaustive coverage is cheap.
            if n <= self.exhaustive_flip_n_max:
                seqs = seqs + _exhaustive_flip_sequences(
                    n, graph, self.problem.directed, include_twins=self.use_twins,
                )
            seqs = self._filter_sequences_for_mode(seqs, graph)
            self._test_sequences[key] = seqs
        return self._test_sequences[key]

    def _filter_sequences_for_mode(
        self,
        seqs: list[list[tuple[str, tuple[int, int]]]],
        graph: np.ndarray,
    ) -> list[list[tuple[str, tuple[int, int]]]]:
        """Keep only the ops ``update_mode`` allows, still legal on the evolving graph.

        This lets a pack declare an incremental or decremental-only problem.
        """
        if self.update_mode == "mixed":
            return seqs
        allowed = "insert" if self.update_mode == "insert_only" else "delete"
        filtered: list[list[tuple[str, tuple[int, int]]]] = []
        for seq in seqs:
            current = graph.copy()
            out: list[tuple[str, tuple[int, int]]] = []
            for op_type, (u, v) in seq:
                if op_type != allowed:
                    continue
                if allowed == "insert":
                    if current[u, v]:
                        continue
                    current[u, v] = 1
                    if not self.problem.directed:
                        current[v, u] = 1
                else:  # delete
                    if not current[u, v]:
                        continue
                    current[u, v] = 0
                    if not self.problem.directed:
                        current[v, u] = 0
                out.append((op_type, (u, v)))
            filtered.append(out)
        return filtered

    def _offline_src(self) -> str:
        return self.problem.offline_source

    def verify(self, candidate: Candidate) -> VerifyResult:
        """Run a candidate through the full test universe.

        The universe is split into chunks of ``chunk_size`` base graphs, each in its
        own sandbox subprocess with its own timeout, so a correct candidate finishes
        each chunk well within it while an infinite loop fails fast. With
        ``workers > 1`` chunks run in a process pool; the candidate stays in its own
        subprocess, so the trust boundary is unchanged. Partials are merged in chunk
        order up to the first failure, so the result equals the serial path.
        """
        candidate.transition(CandidateState.TESTING)

        result = VerifyResult(candidate_id=candidate.id, state=CandidateState.TESTING)

        code_path = Path(candidate.code_path)
        if not code_path.exists():
            result.state = CandidateState.CRASH
            result.error_message = f"Candidate file not found: {code_path}"
            candidate.transition(CandidateState.CRASH)
            candidate.error_message = result.error_message
            return result

        offline_src = self._offline_src() if self.use_offline else ""
        root = 0 if self.problem.needs_root else None

        # Build all test cases (graph + its sequences) in a stable order.
        test_cases: list[dict[str, Any]] = []
        graph_meta: list[tuple[int, int]] = []  # (n, num_sequences) per graph
        total_steps = 0
        for n, graph in self.test_graphs:
            sequences = self.get_sequences(n, graph)
            seq_list: list[list[dict]] = []
            for seq in sequences:
                ops = [{"type": op_type, "edge": list(edge)} for op_type, edge in seq]
                seq_list.append(ops)
                total_steps += 1 + len(seq)  # init + operations
            test_cases.append({
                "graph": graph.tolist(),
                "sequences": seq_list,
            })
            graph_meta.append((n, len(sequences)))

        # Adaptive REPEAT: keep total timed calls under a budget so timing
        # stays meaningful without dominating wall time. Target ~500K total
        # calls (candidate + offline), minimum REPEAT=1.
        timing_budget = 500_000
        timing_multiplier = 2 if offline_src else 1
        if total_steps > 0:
            adaptive_repeat = max(1, timing_budget // (total_steps * timing_multiplier))
        else:
            adaptive_repeat = 20
        adaptive_repeat = min(adaptive_repeat, 20)  # cap at 20

        # Split the test universe into chunks (each becomes one sandbox
        # subprocess). chunk_args[i] = (i, chunk_start, chunk_cases, chunk_meta).
        chunk_starts = list(range(0, len(test_cases), self.chunk_size)) or [0]
        chunk_args = [
            (i, chunk_start,
             test_cases[chunk_start:chunk_start + self.chunk_size],
             graph_meta[chunk_start:chunk_start + self.chunk_size])
            for i, chunk_start in enumerate(chunk_starts)
        ]

        # Running totals, accumulated in chunk order by _merge_partial.
        acc = {"total": 0, "passed": 0, "cand_work": 0, "off_work": 0}

        if self.workers == 1:
            # Serial path: one chunk at a time in the parent, in order.
            for i, chunk_start, chunk_cases, chunk_meta in chunk_args:
                partial = _check_chunk_impl(
                    self.problem, self.sandbox, code_path, chunk_cases, chunk_meta,
                    chunk_start, root, offline_src, adaptive_repeat,
                )
                if self._merge_partial(result, partial, acc):
                    break
        else:
            # Parallel path: a sliding window of ``workers`` chunks in flight.
            # Sandbox subprocesses run concurrently; partials are merged in
            # chunk order so the result is identical to the serial path.
            ctx = {
                "problem_name": self.problem.name,
                "directed": self.problem.directed,
                "root": root,
                "offline_src": offline_src,
                "adaptive_repeat": adaptive_repeat,
                "code_path": str(code_path),
                "timeout_seconds": self.sandbox.timeout,
                "python_path": self.sandbox.python,
            }
            self._merge_parallel(result, chunk_args, ctx, acc)

        result.tests_total = acc["total"]
        result.tests_passed = acc["passed"]

        if result.error_message:
            result.state = CandidateState.CRASH
            candidate.transition(CandidateState.CRASH)
            candidate.error_message = result.error_message
        elif result.timeout:
            result.state = CandidateState.FAIL
            candidate.transition(CandidateState.FAIL)
            candidate.timeout = True
        elif result.failing_case:
            result.state = CandidateState.FAIL
            candidate.transition(CandidateState.FAIL)
        else:
            result.state = CandidateState.PASS
            candidate.transition(CandidateState.PASS)

        result.fitness = acc["passed"] / acc["total"] if acc["total"] > 0 else 0.0
        if acc["off_work"] > 0:
            result.work_ratio = acc["cand_work"] / acc["off_work"]
        # else: leave work_ratio as None (no offline baseline to ratio against)

        _update_candidate(candidate, result)
        return result

    def _merge_partial(self, result: VerifyResult, partial: dict[str, Any],
                       acc: dict[str, int]) -> bool:
        """Merge one chunk's partial result into the running totals.

        Returns True if verification should stop (this chunk timed out,
        crashed, or found the first invariant failure). The merge is
        deterministic in chunk order, so once it returns True, later chunks
        cannot change the result and are ignored.
        """
        if partial["timeout"]:
            result.timeout = True
            result.failing_case = {
                "operation": "timeout",
                "chunk_start": partial["chunk_start"],
                **({"hang": partial["hang"]} if partial.get("hang") else {}),
            }
            return True
        if partial["chunk_crash"]:
            result.error_message = partial["chunk_crash_error"]
            result.failing_case = {"operation": "crash", "error": partial["chunk_crash_error"]}
            return True
        acc["total"] += partial["tests_total"]
        acc["passed"] += partial["tests_passed"]
        acc["cand_work"] += partial["candidate_work"]
        acc["off_work"] += partial["offline_work"]
        if partial["crash"]:
            result.error_message = partial["crash_error"]
            result.failing_case = partial["failing_case"]
            return True
        if partial["failing_case"] is not None:
            result.failing_case = partial["failing_case"]
            return True
        return False

    def _merge_parallel(self, result: VerifyResult, chunk_args: list, ctx: dict,
                        acc: dict[str, int]) -> None:
        """Evaluate chunks in a sliding window and merge in chunk order.

        At most ``self.workers`` chunks are in flight at once. As chunks
        complete (in wall-clock order) their partials are held until it is
        their turn in chunk order, so the merge -- and therefore the result --
        is identical to the serial path. Once a chunk fails, no further chunks
        are submitted and the in-flight ones are drained and ignored.
        """
        n_chunks = len(chunk_args)
        futures: dict[int, concurrent.futures.Future] = {}
        pending: dict[int, dict[str, Any]] = {}
        next_submit = 0
        next_merge = 0
        stopped = False

        def fill() -> None:
            nonlocal next_submit
            while next_submit < n_chunks and len(futures) < self.workers and not stopped:
                i, chunk_start, chunk_cases, chunk_meta = chunk_args[next_submit]
                futures[i] = pool.submit(
                    _worker_check_chunk, ctx, i, chunk_start, chunk_cases, chunk_meta,
                )
                next_submit += 1

        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=self.workers) as pool:
                fill()
                while futures:
                    done, _ = concurrent.futures.wait(
                        list(futures.values()),
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                    for fut in done:
                        idx = next(k for k, v in futures.items() if v is fut)
                        del futures[idx]
                        pending[idx] = fut.result()
                    # Merge in chunk order up to the first failure.
                    while next_merge in pending and not stopped:
                        partial = pending.pop(next_merge)
                        stopped = self._merge_partial(result, partial, acc)
                        next_merge += 1
                    fill()
        except concurrent.futures.process.BrokenProcessPool:
            # A worker died (the OOM killer, a signal): not the candidate's
            # doing, which runs in its own sandbox process. Finish the
            # unmerged chunks serially; the result is the same.
            logger.warning("a verifier worker process died (out of memory?); "
                           "checking the remaining chunks serially")
            for i, chunk_start, chunk_cases, chunk_meta in chunk_args[next_merge:]:
                if stopped:
                    break
                partial = pending.pop(i, None) or _check_chunk_impl(
                    self.problem, self.sandbox, ctx["code_path"], chunk_cases, chunk_meta,
                    chunk_start, ctx["root"], ctx["offline_src"], ctx["adaptive_repeat"])
                stopped = self._merge_partial(result, partial, acc)


# ---------------------------------------------------------------------------
# Per-chunk evaluation, shared by the serial path (in the parent) and the
# parallel path (in a worker), so both give identical partial results.
# ---------------------------------------------------------------------------

def _worker_sandbox(ctx: dict[str, Any]) -> Sandbox:
    """Rebuild a Sandbox in a worker process (the parent's is not picklable)."""
    return Sandbox(
        timeout_seconds=ctx["timeout_seconds"],
        python_path=ctx["python_path"],
        directed=ctx["directed"],
    )


def _worker_check_chunk(ctx: dict[str, Any], i: int, chunk_start: int,
                        chunk_cases: list, chunk_meta: list) -> dict[str, Any]:
    """Worker entry point: rebuild trusted objects and check one chunk.

    Runs in a pool worker process. It rebuilds the problem (via
    ``get_problem``) and the sandbox from plain picklable context, then runs
    the same per-chunk logic as the serial path. The candidate stays isolated
    in its own sandbox subprocess, so the trust boundary is unchanged.
    """
    from .problem_definitions import get_problem

    problem = get_problem(ctx["problem_name"])
    sandbox = _worker_sandbox(ctx)
    return _check_chunk_impl(
        problem, sandbox, ctx["code_path"], chunk_cases, chunk_meta,
        chunk_start, ctx["root"], ctx["offline_src"], ctx["adaptive_repeat"],
    )


HANG_PROBE_SECONDS = 3
HANG_PROBE_MAX_GRAPHS = 400
HANG_PROBE_BUDGET_SECONDS = 60  # total, per timed-out chunk


def _locate_hang(sandbox: Sandbox, code_path, chunk_cases: list[dict[str, Any]],
                 chunk_meta: list[tuple[int, int]], root: int | None) -> dict[str, Any] | None:
    """After a chunk timeout, find the first graph and sequence that hang.

    Re-runs the chunk one base graph at a time (then one sequence at a time)
    with a short timeout, so the reflector gets a concrete failing case
    instead of just "timeout". Bounded: gives up after
    ``HANG_PROBE_MAX_GRAPHS`` graphs or ``HANG_PROBE_BUDGET_SECONDS`` in total.
    """
    deadline = time.monotonic() + HANG_PROBE_BUDGET_SECONDS
    for case, (n, _num) in list(zip(chunk_cases, chunk_meta))[:HANG_PROBE_MAX_GRAPHS]:
        if time.monotonic() > deadline:
            return None
        r = sandbox.execute_batch(code_path, [case], offline_src="", root=root, repeat=1,
                                  timeout=HANG_PROBE_SECONDS)
        if not r.is_timeout:
            continue
        for seq_idx, seq in enumerate(case["sequences"]):
            if time.monotonic() > deadline:
                break
            one = {"graph": case["graph"], "sequences": [seq]}
            r = sandbox.execute_batch(code_path, [one], offline_src="", root=root, repeat=1,
                                      timeout=HANG_PROBE_SECONDS)
            if r.is_timeout:
                ops = [f"{op['type']} ({op['edge'][0]}, {op['edge'][1]})" for op in seq]
                return {"graph_n": n, "graph": case["graph"], "sequence_idx": seq_idx,
                        "operations": ops, "note": f"no result within {HANG_PROBE_SECONDS}s: "
                        "likely an infinite loop in init or one of these updates"}
        return {"graph_n": n, "graph": case["graph"],
                "note": "this graph's sequences together exceed the time limit"}
    return None


def _check_chunk_impl(problem: ProblemDefinition, sandbox: Sandbox,
                      code_path, chunk_cases: list[dict[str, Any]],
                      chunk_meta: list[tuple[int, int]], chunk_start: int,
                      root: int | None, offline_src: str,
                      adaptive_repeat: int) -> dict[str, Any]:
    """Run one chunk's sandbox subprocess and check its invariants.

    Returns a compact, picklable partial result:
      - timeout: the whole chunk subprocess exceeded its wall-clock timeout
      - chunk_crash: the subprocess crashed before producing any results
      - tests_total / tests_passed: sequences accounted for / passed in this
        chunk (counted up to the first failure, matching the serial loop)
      - candidate_work / offline_work: summed timings for the counted sequences
      - crash: a per-sequence crash was hit in this chunk
      - failing_case: the first invariant failure (with its in-chunk position)
        or the first crash; None if the chunk is fully clean
    """
    batch_result = sandbox.execute_batch(
        code_path, chunk_cases, offline_src=offline_src, root=root,
        repeat=adaptive_repeat,
    )

    if batch_result.is_timeout:
        return {
            "chunk_start": chunk_start, "timeout": True,
            "tests_total": 0, "tests_passed": 0,
            "candidate_work": 0, "offline_work": 0,
            "crash": False, "chunk_crash": False,
            "chunk_crash_error": None, "failing_case": None,
            "hang": _locate_hang(sandbox, code_path, chunk_cases, chunk_meta, root),
        }

    if batch_result.is_crash and not batch_result.all_results:
        return {
            "chunk_start": chunk_start, "timeout": False,
            "tests_total": 0, "tests_passed": 0,
            "candidate_work": 0, "offline_work": 0,
            "crash": False, "chunk_crash": True,
            "chunk_crash_error": batch_result.error, "failing_case": None,
        }

    all_results = batch_result.all_results or []
    tests_total = 0
    passed_tests = 0
    candidate_work = 0
    offline_work = 0
    failing_case = None
    crash = False
    crash_error = None

    for local_g_idx, (n, num_seqs) in enumerate(chunk_meta):
        graph_results = all_results[local_g_idx] if local_g_idx < len(all_results) else []
        original_graph = np.array(chunk_cases[local_g_idx]["graph"], dtype=int)

        for seq_idx in range(num_seqs):
            tests_total += 1

            seq_result = graph_results[seq_idx] if seq_idx < len(graph_results) else None
            if seq_result is None:
                failing_case = {
                    "graph_n": n, "sequence_idx": seq_idx,
                    "operation": "missing result",
                }
                break

            if seq_result.get("status") == "crash":
                crash = True
                crash_error = seq_result.get("error")
                failing_case = {
                    "graph_n": n, "sequence_idx": seq_idx,
                    "operation": "crash",
                    "error": seq_result.get("error"),
                }
                break

            # Use partial results if available (crash mid-sequence)
            results = seq_result.get("results") or seq_result.get("partial_results") or []
            candidate_times = seq_result.get("timings") or seq_result.get("partial_timings") or []
            offline_times = seq_result.get("offline_timings") or seq_result.get("partial_offline_timings") or []

            if not results:
                failing_case = {
                    "graph_n": n, "sequence_idx": seq_idx,
                    "operation": "no results from sandbox",
                }
                break

            # Replay operations on a copy of the graph to check invariants.
            # The sequence is recovered from the chunk's own test case (the
            # ops list), so the worker needs no access to the parent's cache.
            seq_ops = chunk_cases[local_g_idx]["sequences"][seq_idx]
            # A finished sequence has a state and a timing per step; a forged
            # result channel must not pass by leaving steps out.
            if seq_result.get("status") == "ok" and not (
                    len(results) == len(candidate_times) == len(seq_ops) + 1):
                failing_case = {
                    "graph_n": n, "sequence_idx": seq_idx,
                    "operation": "incomplete results from sandbox",
                }
                break
            current_graph = original_graph.copy()

            state = _deserialize_state(results[0]["state"])
            if not _invariant_holds(problem, state, current_graph, root):
                failing_case = _failing_context(problem, state, current_graph, root)
                failing_case["graph_n"] = n
                failing_case["sequence_idx"] = seq_idx
                failing_case["operation"] = "init"
                break

            if candidate_times:
                candidate_work += candidate_times[0]
            if offline_times:
                offline_work += offline_times[0]

            found = False
            for step_idx, op in enumerate(seq_ops):
                op_type = op["type"]
                u, v = op["edge"]
                if op_type == "insert":
                    current_graph[u, v] = 1
                    if not problem.directed:
                        current_graph[v, u] = 1
                elif op_type == "delete":
                    current_graph[u, v] = 0
                    if not problem.directed:
                        current_graph[v, u] = 0

                step_result_idx = step_idx + 1
                if step_result_idx < len(results):
                    state = _deserialize_state(results[step_result_idx]["state"])
                    if not _invariant_holds(problem, state, current_graph, root):
                        failing_case = _failing_context(problem, state, current_graph, root)
                        failing_case["graph_n"] = n
                        failing_case["sequence_idx"] = seq_idx
                        failing_case["operation"] = f"{op_type} ({u}, {v})"
                        found = True
                        break

                if step_result_idx < len(candidate_times):
                    candidate_work += candidate_times[step_result_idx]
                if step_result_idx < len(offline_times):
                    offline_work += offline_times[step_result_idx]

            if found:
                break

            passed_tests += 1

        if failing_case is not None or crash:
            break

    return {
        "chunk_start": chunk_start, "timeout": False,
        "tests_total": tests_total, "tests_passed": passed_tests,
        "candidate_work": candidate_work, "offline_work": offline_work,
        "crash": crash, "crash_error": crash_error,
        "chunk_crash": False, "chunk_crash_error": None,
        "failing_case": failing_case,
    }


def _invariant_holds(problem: ProblemDefinition, state: Any, graph: np.ndarray,
                     root: int | None) -> bool:
    """check_invariant that treats a malformed candidate state as a failure.

    A candidate controls its state's shape; a checker exception on odd values
    (wrong types, None where an int is expected) must fail that candidate, not
    abort the whole run.
    """
    try:
        return bool(problem.check_invariant(state, graph, root))
    except Exception:
        return False


def _failing_context(problem: ProblemDefinition, state: Any, graph: np.ndarray,
                     root: int | None) -> dict[str, Any]:
    """failing_context that survives the malformed states _invariant_holds rejects."""
    try:
        return problem.failing_context(state, graph, root)
    except Exception as e:
        return {"problem": problem.name, "result": repr(state)[:500],
                "graph": graph.tolist(), "checker_error": f"{type(e).__name__}: {e}"}


def _deserialize_state(raw: Any) -> Any:
    """Convert JSON-deserialized state back to Python objects for invariant checking."""
    if isinstance(raw, dict):
        return {k: _deserialize_state(v) for k, v in raw.items()}
    if isinstance(raw, list):
        # Could be a list of integers (set) or a list of lists (components)
        return [_deserialize_state(x) for x in raw]
    return raw


def _update_candidate(candidate: Candidate, result: VerifyResult) -> None:
    """Update candidate fields from verification result."""
    candidate.fitness = result.fitness
    candidate.work_ratio = result.work_ratio
    candidate.timeout = result.timeout
    candidate.tests_passed = result.tests_passed
    candidate.tests_total = result.tests_total
    candidate.error_message = result.error_message
    candidate.failing_case = result.failing_case
