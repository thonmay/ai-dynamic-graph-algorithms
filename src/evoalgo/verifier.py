"""Verifier and Evaluator: test candidates against invariants.

The Verifier runs each candidate through the bounded test universe:
  1. For each base graph in the test set
  2. Generate operation sequences (insert/delete)
  3. Execute candidate in sandbox (init + replay operations)
  4. After each operation, check the invariant against the oracle
  5. Record pass/fail, failing case, work counts

The Evaluator computes fitness (fraction of sequences passing) and
work_ratio (candidate_work / offline_work).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .candidate import Candidate, CandidateState
from .graph_generator import (
    generate_test_graphs,
    generate_operation_sequences,
)
from .problem_definitions import ProblemDefinition
from .sandbox import Sandbox, SandboxResult

logger = logging.getLogger(__name__)


def _exhaustive_flip_sequences(
    n: int,
    graph: np.ndarray,
    directed: bool,
) -> list[list[tuple[str, tuple[int, int]]]]:
    """Deterministic short update sequences covering the update space for small n.

    Returns all legal single-edge flips (each as a length-1 sequence) plus a
    compact set of length-2 paths (flip one edge, then flip each other edge).
    This closes the coverage hole left by random sequences: a reachable
    counterexample at n<=exhaustive_flip_n_max is now hit deterministically.
    """
    pairs = [(u, v) for u in range(n) for v in range(n) if u != v and (directed or u < v)]
    single: list[list[tuple[str, tuple[int, int]]]] = []
    twins: list[list[tuple[str, tuple[int, int]]]] = []
    for u, v in pairs:
        if graph[u, v]:
            single.append([("delete", (u, v))])
        else:
            single.append([("insert", (u, v))])
    # length-2 paths: first flip (u,v), then flip (u',v') in the resulting graph
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
    per_step_states: list[dict] = field(default_factory=list)


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
    ):
        self.problem = problem
        self.sandbox = sandbox
        self.n_max = bound_n_max
        self.n_random = bound_n_random
        self.seq_len_max = bound_seq_len_max
        self.seq_count = bound_seq_count
        self.seed = bound_seed
        self.exhaustive_flip_n_max = exhaustive_flip_n_max

        # Cache test graphs (they don't change between candidates)
        self._test_graphs: list[tuple[int, np.ndarray]] | None = None
        self._test_sequences: dict[int, list[list[tuple[str, tuple[int, int]]]]] = {}

    @property
    def test_graphs(self) -> list[tuple[int, np.ndarray]]:
        if self._test_graphs is None:
            self._test_graphs = generate_test_graphs(
                self.n_max, self.n_random, self.seed,
                directed=self.problem.directed,
            )
            logger.info("Generated %d test graphs (n=2..%d, %s)",
                        len(self._test_graphs), self.n_max,
                        "directed" if self.problem.directed else "undirected")
        return self._test_graphs

    def get_sequences(self, n: int, graph: np.ndarray) -> list[list[tuple[str, tuple[int, int]]]]:
        key = (n, graph.tobytes())
        if key not in self._test_sequences:
            seqs = generate_operation_sequences(
                n, graph, self.seq_len_max, self.seq_count, self.seed + n,
                directed=self.problem.directed,
            )
            # Deterministic exhaustive short sequences for small n: every
            # single-edge flip plus a compact set of 2-flip paths. Random
            # sequences alone missed reachable counterexamples (e.g. a single
            # insert breaking dynamic MCS at n=3), so close that gap for the
            # sizes where exhaustive coverage is cheap.
            if n <= self.exhaustive_flip_n_max:
                seqs = seqs + _exhaustive_flip_sequences(n, graph, self.problem.directed)
            self._test_sequences[key] = seqs
        return self._test_sequences[key]

    def _offline_src(self) -> str:
        """Return the offline baseline source for the sandbox subprocess.

        Uses the problem's offline_source property which provides a
        self-contained function named offline_compute(graph, root).
        """
        return self.problem.offline_source

    def verify(self, candidate: Candidate) -> VerifyResult:
        """Run a candidate through the full test universe.

        All test cases are batched into a single sandbox subprocess to
        avoid per-call subprocess overhead (~160ms/call). The runner
        executes every (graph, sequence) pair and returns per-sequence
        results. We then process results in order, stopping at the
        first failure for fitness scoring.
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

        offline_src = self._offline_src()
        root = 0 if self.problem.needs_root else None

        # Build all test cases for batched execution
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

        # Adaptive REPEAT: keep total timed calls under a budget so the
        # sandbox doesn't time out on large test universes. Target ~500K
        # total calls (candidate + offline), minimum REPEAT=1.
        TIMING_BUDGET = 500_000
        timing_multiplier = 2 if offline_src else 1
        if total_steps > 0:
            adaptive_repeat = max(1, TIMING_BUDGET // (total_steps * timing_multiplier))
        else:
            adaptive_repeat = 20
        adaptive_repeat = min(adaptive_repeat, 20)  # cap at 20

        # Single subprocess for all test cases
        batch_result = self.sandbox.execute_batch(
            code_path, test_cases, offline_src=offline_src, root=root,
            repeat=adaptive_repeat,
        )

        if batch_result.is_timeout:
            result.timeout = True
            result.state = CandidateState.FAIL
            result.failing_case = {"operation": "timeout"}
            candidate.transition(CandidateState.FAIL)
            candidate.timeout = True
            _update_candidate(candidate, result)
            return result

        if batch_result.is_crash and not batch_result.all_results:
            result.error_message = batch_result.error
            result.failing_case = {"operation": "crash", "error": batch_result.error}
            candidate.transition(CandidateState.CRASH)
            candidate.error_message = batch_result.error
            result.state = CandidateState.CRASH
            _update_candidate(candidate, result)
            return result

        # Process results: iterate graphs and sequences in order
        all_results = batch_result.all_results or []
        total_tests = 0
        passed_tests = 0
        candidate_work = 0
        offline_work = 0
        found_failure = False

        for g_idx, (n, num_seqs) in enumerate(graph_meta):
            if found_failure:
                break
            graph_results = all_results[g_idx] if g_idx < len(all_results) else []
            original_graph = self.test_graphs[g_idx][1]  # np.ndarray

            for seq_idx in range(num_seqs):
                total_tests += 1

                seq_result = graph_results[seq_idx] if seq_idx < len(graph_results) else None
                if seq_result is None:
                    result.failing_case = {
                        "graph_n": n, "sequence_idx": seq_idx,
                        "operation": "missing result",
                    }
                    found_failure = True
                    break

                if seq_result.get("status") == "crash":
                    result.error_message = seq_result.get("error")
                    result.failing_case = {
                        "graph_n": n, "sequence_idx": seq_idx,
                        "operation": "crash",
                        "error": seq_result.get("error"),
                    }
                    candidate.transition(CandidateState.CRASH)
                    candidate.error_message = seq_result.get("error")
                    result.state = CandidateState.CRASH
                    result.tests_total = total_tests
                    result.tests_passed = passed_tests
                    result.fitness = passed_tests / total_tests if total_tests > 0 else 0.0
                    _update_candidate(candidate, result)
                    return result

                # Use partial results if available (crash mid-sequence)
                results = seq_result.get("results") or seq_result.get("partial_results") or []
                candidate_times = seq_result.get("timings") or seq_result.get("partial_timings") or []
                offline_times = seq_result.get("offline_timings") or seq_result.get("partial_offline_timings") or []

                if not results:
                    result.failing_case = {
                        "graph_n": n, "sequence_idx": seq_idx,
                        "operation": "no results from sandbox",
                    }
                    found_failure = True
                    break

                # Replay operations on a copy of the graph to check invariants
                current_graph = original_graph.copy()
                sequences = self.get_sequences(n, original_graph)
                seq = sequences[seq_idx]

                # Check init state
                state = _deserialize_state(results[0]["state"])
                if not self.problem.check_invariant(state, current_graph, root):
                    result.failing_case = self.problem.failing_context(
                        state, current_graph, root
                    )
                    result.failing_case["graph_n"] = n
                    result.failing_case["sequence_idx"] = seq_idx
                    result.failing_case["operation"] = "init"
                    found_failure = True
                    break

                if candidate_times:
                    candidate_work += candidate_times[0]
                if offline_times:
                    offline_work += offline_times[0]

                # Check after each operation
                for step_idx, (op_type, edge) in enumerate(seq):
                    u, v = edge
                    if op_type == "insert":
                        current_graph[u, v] = 1
                        if not self.problem.directed:
                            current_graph[v, u] = 1
                    elif op_type == "delete":
                        current_graph[u, v] = 0
                        if not self.problem.directed:
                            current_graph[v, u] = 0

                    step_result_idx = step_idx + 1
                    if step_result_idx < len(results):
                        state = _deserialize_state(results[step_result_idx]["state"])
                        if not self.problem.check_invariant(state, current_graph, root):
                            result.failing_case = self.problem.failing_context(
                                state, current_graph, root
                            )
                            result.failing_case["graph_n"] = n
                            result.failing_case["sequence_idx"] = seq_idx
                            result.failing_case["operation"] = f"{op_type} {edge}"
                            found_failure = True
                            break

                    if step_result_idx < len(candidate_times):
                        candidate_work += candidate_times[step_result_idx]
                    if step_result_idx < len(offline_times):
                        offline_work += offline_times[step_result_idx]

                if found_failure:
                    break

                passed_tests += 1

        result.tests_total = total_tests
        result.tests_passed = passed_tests

        if found_failure and result.timeout:
            result.state = CandidateState.FAIL
            candidate.transition(CandidateState.FAIL)
            candidate.timeout = True
        elif found_failure:
            result.state = CandidateState.FAIL
            candidate.transition(CandidateState.FAIL)
        else:
            result.state = CandidateState.PASS
            candidate.transition(CandidateState.PASS)

        result.fitness = passed_tests / total_tests if total_tests > 0 else 0.0
        if offline_work > 0:
            result.work_ratio = candidate_work / offline_work
        # else: leave work_ratio as None (no offline baseline to ratio against)

        _update_candidate(candidate, result)
        return result


class Evaluator:
    """Computes fitness and work_ratio from verification results."""

    @staticmethod
    def score(result: VerifyResult) -> tuple[float, float | None, bool]:
        """Return (fitness, work_ratio, is_efficiency_improvement)."""
        is_improvement = (
            result.fitness == 1.0
            and result.work_ratio is not None
            and result.work_ratio < 1.0
        )
        return result.fitness, result.work_ratio, is_improvement


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
