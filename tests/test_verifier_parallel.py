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
