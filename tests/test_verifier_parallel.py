# AI-assisted code: generated and revised with Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Parallel chunk evaluation: timeout semantics and worker determinism.

The infinite-loop tests confirm that a candidate that loops forever on one
case still FAILs with a timeout within roughly one per-chunk timeout, both on
the serial path (workers=1) and the parallel path (workers>1). The parallel
path runs every chunk's sandbox subprocess concurrently, so the wall time is
bounded by a single per-chunk timeout plus pool overhead, not by the number of
chunks.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from evoalgo.candidate import Candidate
from evoalgo.problem_definitions import get_problem
from evoalgo.sandbox import Sandbox
from evoalgo.verifier import Verifier


# A candidate whose init() loops forever. Every graph's init hangs, so every
# chunk's sandbox subprocess hits its wall-clock timeout.
_INFINITE_LOOP_CODE = '''
def init(graph):
    while True:
        pass
    return {}

def insert_edge(graph, edge, state):
    return state

def delete_edge(graph, edge, state):
    return state
'''


def _make_verifier(workers: int, chunk_size: int, timeout: int) -> Verifier:
    problem = get_problem("dynamic_bfs")
    sandbox = Sandbox(timeout_seconds=timeout, directed=problem.directed)
    return Verifier(
        problem=problem,
        sandbox=sandbox,
        bound_n_max=3,
        bound_n_random=0,
        bound_seq_len_max=10,
        bound_seq_count=3,
        bound_seed=42,
        use_offline=False,
        relabels_per_class=0,
        chunk_size=chunk_size,
        workers=workers,
    )


def _verify_infinite_loop(workers: int, chunk_size: int, timeout: int,
                          tmp_path: Path) -> tuple:
    verifier = _make_verifier(workers, chunk_size, timeout)
    path = tmp_path / f"infinite_w{workers}.py"
    path.write_text(_INFINITE_LOOP_CODE)
    cand = Candidate(id=f"infinite_w{workers}", code_path=str(path), generation=0)
    t0 = time.time()
    result = verifier.verify(cand)
    wall = time.time() - t0
    return cand.state.value, result.timeout, wall


def test_infinite_loop_times_out_serial(tmp_path):
    """workers=1: an infinite-loop candidate FAILs with a timeout quickly."""
    state, timed_out, wall = _verify_infinite_loop(1, 10, 5, tmp_path)
    assert state == "FAIL", state
    assert timed_out is True
    # Serial: only the first chunk runs (it times out and stops the merge), so
    # wall time is ~one per-chunk timeout plus overhead -- far below the full
    # universe.
    assert wall < 25, f"serial infinite-loop verify took {wall:.1f}s"


def test_infinite_loop_times_out_parallel(tmp_path):
    """workers=8: an infinite-loop candidate FAILs with a timeout quickly.

    All chunks run their sandbox subprocesses concurrently; each hits the
    per-chunk timeout, and the merge stops at the first (chunk 0). Wall time
    must stay within roughly one per-chunk timeout plus pool overhead.
    """
    state, timed_out, wall = _verify_infinite_loop(8, 10, 5, tmp_path)
    assert state == "FAIL", state
    assert timed_out is True
    assert wall < 25, f"parallel infinite-loop verify took {wall:.1f}s"


def test_infinite_loop_parallel_no_slower_than_serial(tmp_path):
    """Parallel must not be slower than serial for a timeout candidate.

    Both are bounded by ~one per-chunk timeout, but the parallel path should
    not regress (e.g. by serializing the timeouts). Allow generous slack.
    """
    _, _, wall_serial = _verify_infinite_loop(1, 10, 5, tmp_path)
    _, _, wall_parallel = _verify_infinite_loop(8, 10, 5, tmp_path)
    assert wall_parallel < wall_serial + 15, (wall_parallel, wall_serial)


def test_hang_is_located(tmp_path):
    """A timeout reports the first graph and sequence that hang."""
    verifier = _make_verifier(1, 10, 5)
    path = tmp_path / "hang.py"
    path.write_text(_INFINITE_LOOP_CODE)
    result = verifier.verify(Candidate(id="hang", code_path=str(path), generation=0))
    hang = result.failing_case["hang"]
    assert hang["graph_n"] >= 1 and "graph" in hang


# Correct BFS that spells unreachable distances as None (a valid convention).
_NONE_DIST_BFS = '''
from collections import deque

def init(graph):
    n = len(graph)
    parent = [None] * n
    dist = [None] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        for v in range(n):
            if graph[u][v] and dist[v] is None:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return {"parent": parent, "distances": dist}

def insert_edge(graph, edge, state):
    return init(graph)

def delete_edge(graph, edge, state):
    return init(graph)
'''

# A malformed state must fail the candidate, not crash the verifier.
_MALFORMED_STATE = _NONE_DIST_BFS.replace(
    'return {"parent": parent, "distances": dist}',
    'return {"parent": parent, "distances": ["x"] * n}')


@pytest.mark.parametrize("workers", [1, 4])
def test_none_distances_pass(tmp_path, workers):
    path = tmp_path / "none_dist.py"
    path.write_text(_NONE_DIST_BFS)
    cand = Candidate(id="none_dist", code_path=str(path), generation=0)
    _make_verifier(workers, 10, 30).verify(cand)
    assert cand.state.value == "PASS", cand.failing_case


@pytest.mark.parametrize("workers", [1, 4])
def test_malformed_state_fails_cleanly(tmp_path, workers):
    path = tmp_path / "malformed.py"
    path.write_text(_MALFORMED_STATE)
    cand = Candidate(id="malformed", code_path=str(path), generation=0)
    _make_verifier(workers, 10, 30).verify(cand)
    assert cand.state.value == "FAIL"


def test_dfs_requires_finish():
    """Without finish only a weak replay check exists; it accepts forward-cross edges."""
    import numpy as np
    p = get_problem("dynamic_dfs")
    g = np.array([[0, 1, 1], [0, 0, 1], [0, 0, 0]])
    assert not p.check_invariant({"parent": [None, 0, 0], "discover": [0, 1, 2]}, g, 0)
    good = {"parent": [None, 0, 1], "discover": [0, 1, 2], "finish": [5, 4, 3]}
    assert p.check_invariant(good, g, 0)


def test_failing_context_survives_malformed_state():
    import numpy as np
    from evoalgo.verifier import _failing_context, _invariant_holds
    p = get_problem("dynamic_lbfs")
    g = np.zeros((3, 3), dtype=int)
    bad = {"ordering": ["a", 1, 2]}
    assert not _invariant_holds(p, bad, g, None)
    ctx = _failing_context(p, bad, g, None)
    assert "checker_error" in ctx


def test_dfs_rejects_parent_that_did_not_discover():
    """Real DFS times, but parent[2] = 0 although 1 discovered 2 (0->1->2 with
    the forward edge 0->2): no DFS produces this tree."""
    import numpy as np
    p = get_problem("dynamic_dfs")
    g = np.array([[0, 1, 1], [0, 0, 1], [0, 1, 0]])
    bad = {"parent": [None, 0, 0], "discover": [0, 1, 2], "finish": [5, 4, 3]}
    assert not p.check_invariant(bad, g, 0)
    assert not p.check_invariant({**bad, "finish": {}}, g, 0)
    assert p.check_invariant({**bad, "parent": [None, 0, 1]}, g, 0)


def test_scc_rejects_split_cycle_through_three_components():
    """Pairwise merging finds no mutually reachable pair in a 3-cycle split
    into singletons; the triple is one SCC."""
    import numpy as np
    p = get_problem("dynamic_scc")
    g = np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
    assert not p.check_invariant({"components": [[0], [1], [2]]}, g, None)
    assert p.check_invariant({"components": [[2, 0, 1]]}, g, None)


def test_dfs_checker_rejects_nan_parent_cycle_without_hanging():
    import numpy as np
    p = get_problem("dynamic_dfs")
    g = np.array([[0, 1, 0], [0, 0, 1], [0, 1, 0]])
    nan = float("nan")
    assert not p.check_invariant({"parent": [None, 2, 1], "discover": [0, nan, nan],
                                  "finish": [5, nan, nan]}, g, 0)
    assert not p.check_invariant({"parent": [None, 0, 1], "discover": [0, 1.0, 2],
                                  "finish": [5, 4, 3]}, g, 0)
    assert p.check_invariant({"parent": [None, 0, 1], "discover": [0, 1, 2],
                              "finish": [5, 4, 3]}, g, 0)
