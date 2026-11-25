# AI-assisted code: generated and revised with Qwen3.8-27B and Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Verifier self-test: nauty universe, decoder, relabeling, fault corpus.

Covers contribution 2 of the topic proposal: an exhaustive correctness checker
that enumerates all non-isomorphic digraphs up to size n (via nauty), applies
every single-edge operation, and compares the candidate's incremental output
against offline recomputation. The completion signal is that the engine
validates known-good algorithms and rejects known-bad mutations with zero
false negatives on n <= 5.

Tests:
  - digraph6 decoder round-trip and class counts per n (OEIS A000273, A353996)
  - rooted counts and loop-free / distinct invariants
  - deterministic relabeling (same seed -> same universe)
  - the fault corpus: every real fault rejected at n<=5, equivalent controls
    accepted (proves the checker is invariant-based, not tie-broken)

The fault-corpus tests are marked ``slow`` (they run the full n<=5 universe
once per candidate) but are executed in a normal ``pytest`` run.
"""

from __future__ import annotations

import copy
import os
from pathlib import Path

import numpy as np
import pytest

from evoalgo.candidate import Candidate
from evoalgo.graph_generator import (
    NAUTY_DATA_DIR,
    decode_digraph6,
    encode_digraph6,
    digraph_rows_to_matrix,
    generate_test_graphs,
    load_nauty_digraphs,
    load_nauty_rooted_digraphs,
    relabel_digraph,
)
from evoalgo.problem_definitions import get_problem
from evoalgo.sandbox import Sandbox
from evoalgo.selftest.faults import (
    FAULTS,
    compose_fault_code,
    counterexample_graph,
    equivalent_controls,
    faults_for,
    real_faults,
)
from evoalgo.selftest.references import reference_code
from evoalgo.verifier import Verifier

# Expected non-isomorphic digraph counts (OEIS A000273).
DIRECTED_COUNTS = {1: 1, 2: 3, 3: 16, 4: 218, 5: 9608}
# Expected (digraph, root-orbit) class counts (OEIS A353996).
ROOTED_COUNTS = {1: 1, 2: 4, 3: 36, 4: 752, 5: 45960}

# Problems that have a reference + fault corpus in the self-test.
CORPUS_PROBLEMS = ("dynamic_bfs", "dynamic_dfs", "dynamic_lbfs")
# Real faults per problem in the corpus.
REAL_FAULTS = {"dynamic_bfs": 14, "dynamic_dfs": 15, "dynamic_lbfs": 12}


# ---------------------------------------------------------------------------
# Decoder round-trip and class counts
# ---------------------------------------------------------------------------

def test_digraph6_round_trip_formats_example():
    # nauty formats.txt example: n=5, arcs 0->2, 0->4, 3->1, 3->4.
    n, rows = decode_digraph6("&DI?AO?")
    mat = digraph_rows_to_matrix(n, rows)
    arcs = [(i, j) for i in range(n) for j in range(n) if mat[i][j]]
    assert n == 5 and arcs == [(0, 2), (0, 4), (3, 1), (3, 4)]
    assert encode_digraph6(n, rows) == "&DI?AO?"


def test_digraph6_round_trip_empty():
    n, rows = decode_digraph6("&D?????")
    assert n == 5 and rows == [0, 0, 0, 0, 0]
    assert encode_digraph6(n, rows) == "&D?????"


def test_digraph6_round_trip_all_files():
    for prefix, counts in (("directed", DIRECTED_COUNTS), ("rooted", ROOTED_COUNTS)):
        for n, expected in counts.items():
            path = NAUTY_DATA_DIR / f"{prefix}_n{n}.d6"
            lines = [l for l in path.read_text().splitlines() if l.strip()]
            assert len(lines) == expected, (prefix, n, len(lines), expected)
            seen = set()
            for line in lines:
                dn, rows = decode_digraph6(line)
                assert dn == n
                for i in range(n):
                    assert (rows[i] >> i) & 1 == 0, "loop found"
                assert tuple(rows) not in seen, "duplicate class"
                seen.add(tuple(rows))
                assert encode_digraph6(n, rows) == line, "round-trip mismatch"


def test_class_counts_directed():
    for n, expected in DIRECTED_COUNTS.items():
        assert len(load_nauty_digraphs(n)) == expected, n


def test_class_counts_rooted():
    for n, expected in ROOTED_COUNTS.items():
        assert len(load_nauty_rooted_digraphs(n)) == expected, n


def test_rooted_root_is_at_vertex_zero():
    # In a rooted representative the distinguished vertex is relabeled to 0,
    # so vertex 0 must be a valid root (it need not be isolated, but the file
    # is one line per root orbit). We only assert the structural invariant:
    # every line decodes to n vertices and is loop-free.
    for n in (2, 3):
        for g in load_nauty_rooted_digraphs(n):
            assert g.shape == (n, n)
            assert not np.any(np.diag(g))


# ---------------------------------------------------------------------------
# Relabel determinism and universe assembly
# ---------------------------------------------------------------------------

def test_relabel_determinism():
    g = load_nauty_digraphs(3)[0]
    # identity relabel is a no-op
    assert np.array_equal(relabel_digraph(g, tuple(range(3))), g)
    # a fixed permutation is deterministic
    perm = (2, 0, 1)
    a = relabel_digraph(g, perm)
    b = relabel_digraph(g, perm)
    assert np.array_equal(a, b)
    # relabeling preserves the edge count (isomorphism)
    assert a.sum() == g.sum()


def test_universe_deterministic_across_calls():
    kwargs = dict(n_max=3, n_random=5, seed=1337, directed=True,
                  universe="nauty", rooted=True, relabels_per_class=2)
    a = generate_test_graphs(**kwargs)
    b = generate_test_graphs(**kwargs)
    assert len(a) == len(b)
    for (na, ga), (nb, gb) in zip(a, b):
        assert na == nb
        assert np.array_equal(ga, gb)


def test_universe_relabels_scale():
    # k relabels per class -> (1+k) base graphs per class, but capped by the
    # number of distinct non-identity permutations (n!-1) at that size.
    import math
    for k in (0, 1, 2):
        g = generate_test_graphs(n_max=3, n_random=0, seed=1337, directed=True,
                                 universe="nauty", rooted=True,
                                 relabels_per_class=k)
        expected = sum(
            ROOTED_COUNTS[n] * (1 + min(k, math.factorial(n) - 1))
            for n in (2, 3)
        )
        assert len(g) == expected, (k, len(g), expected)


def test_relabel_cap_at_n2():
    # n=2 has only one non-identity permutation, so k=2 yields just one
    # relabel (the universe is capped by the number of distinct permutations).
    g = generate_test_graphs(n_max=2, n_random=0, seed=1337, directed=True,
                             universe="nauty", rooted=True,
                             relabels_per_class=2)
    assert len(g) == ROOTED_COUNTS[2] * 2  # 4 classes x (1 + 1 relabel)


def test_undirected_mcs_path_unchanged():
    # MCS (undirected) keeps the labeled n<=5 + nauty n>5 behaviour.
    g = generate_test_graphs(n_max=6, n_random=5, seed=1337, directed=False,
                             universe="nauty", rooted=False, relabels_per_class=0)
    counts = {}
    for n, _ in g:
        counts[n] = counts.get(n, 0) + 1
    assert counts == {2: 2, 3: 8, 4: 64, 5: 1024, 6: 156}


def test_labeled_universe_flag():
    # The documented labeled comparison mode still produces all labeled
    # digraphs for n <= exhaustive_cap (4): 2^(n(n-1)) per n.
    g = generate_test_graphs(n_max=3, n_random=5, seed=1337, directed=True,
                             universe="labeled", rooted=False, relabels_per_class=0)
    counts = {}
    for n, _ in g:
        counts[n] = counts.get(n, 0) + 1
    assert counts == {2: 2 ** 2, 3: 2 ** 6}  # 2^(n(n-1))


# ---------------------------------------------------------------------------
# Fault corpus: zero false negatives at n<=5
# ---------------------------------------------------------------------------

def _make_verifier(problem_name: str, n_max: int, chunk_size: int = 2000,
                   workers: int | None = None) -> Verifier:
    problem = get_problem(problem_name)
    sandbox = Sandbox(timeout_seconds=120, directed=problem.directed)
    return Verifier(
        problem=problem,
        sandbox=sandbox,
        bound_n_max=n_max,
        bound_n_random=0,
        bound_seq_len_max=10,
        bound_seq_count=3,
        bound_seed=42,
        use_offline=False,
        relabels_per_class=0,
        chunk_size=chunk_size,
        workers=workers,
    )


def _write_candidate(tmp_path: Path, name: str, code: str) -> Path:
    p = tmp_path / f"{name}.py"
    p.write_text(code)
    return p


def _verify_code(problem_name: str, code: str, n_max: int, tmp_path: Path) -> Candidate:
    verifier = _make_verifier(problem_name, n_max)
    path = _write_candidate(tmp_path, problem_name, code)
    cand = Candidate(id=f"{problem_name}_{tmp_path.name}", code_path=str(path), generation=0)
    verifier.verify(cand)
    return cand


@pytest.mark.slow
def test_known_good_references_pass_n5(tmp_path):
    """The known-good validate-or-rebuild references must PASS at n<=5."""
    for pname in CORPUS_PROBLEMS:
        cand = _verify_code(pname, reference_code(pname), 5, tmp_path)
        assert cand.state.value == "PASS", (pname, cand.state.value, cand.failing_case)


@pytest.mark.slow
def test_equivalent_controls_accepted_n5(tmp_path):
    """Equivalent controls (valid variants) must be ACCEPTED at n<=5.

    This proves the checker is invariant-based and not biased to one
    tie-break: a different-but-valid tree/forest must pass.
    """
    for pname in CORPUS_PROBLEMS:
        for ctrl in equivalent_controls(pname):
            cand = _verify_code(pname, compose_fault_code(pname, ctrl), 5, tmp_path)
            assert cand.state.value == "PASS", (pname, ctrl["id"], cand.state.value)


@pytest.mark.slow
def test_real_faults_rejected_n5(tmp_path):
    """Every real (non-equivalent) fault must be REJECTED at n<=5.

    Zero false negatives: |{f in F : verifier accepts f}| == 0.
    """
    for pname in CORPUS_PROBLEMS:
        for fault in real_faults(pname):
            cand = _verify_code(pname, compose_fault_code(pname, fault), 5, tmp_path)
            assert cand.state.value in ("FAIL", "CRASH"), (
                pname, fault["id"], cand.state.value,
            )


# ---------------------------------------------------------------------------
# Parallel chunk evaluation must reproduce the serial semantics exactly
# ---------------------------------------------------------------------------

def _verify_tuple(verifier: Verifier, code: str, tmp_path: Path, name: str) -> tuple:
    """Verify ``code`` and return the comparable fields of the result."""
    path = _write_candidate(tmp_path, name, code)
    cand = Candidate(id=name, code_path=str(path), generation=0)
    result = verifier.verify(cand)
    return (
        cand.state.value,
        result.fitness,
        result.tests_total,
        result.tests_passed,
        result.failing_case,
        result.timeout,
    )


@pytest.mark.slow
def test_parallel_workers_match_serial_n4(tmp_path):
    """workers=1 and workers=4 give identical VerifyResults at n<=4.

    The parallel merge is deterministic in chunk order, so it must reproduce
    the serial semantics exactly: same state, fitness, tests_total,
    tests_passed, failing_case and timeout for a known-good reference and two
    real faults. This is the regression guard for the ProcessPoolExecutor
    refactor (item 2 of the parallel-verification change).

    A small chunk_size (200) forces the ~792-graph n<=4 universe to split into
    4 chunks, so the test genuinely exercises the cross-chunk merge (summing
    chunks before the first failing chunk, and stopping at it) rather than the
    degenerate single-chunk case.
    """
    for pname in CORPUS_PROBLEMS:
        codes = {
            "known-good": reference_code(pname),
            "fault0": compose_fault_code(pname, real_faults(pname)[0]),
            "fault1": compose_fault_code(pname, real_faults(pname)[1]),
        }
        for label, code in codes.items():
            serial = _verify_tuple(
                _make_verifier(pname, 4, chunk_size=200, workers=1),
                code, tmp_path, f"{pname}_{label}_serial",
            )
            parallel = _verify_tuple(
                _make_verifier(pname, 4, chunk_size=200, workers=4),
                code, tmp_path, f"{pname}_{label}_parallel",
            )
            assert serial == parallel, (pname, label, serial, parallel)


def _dies_on_chunk_1(ctx, i, *args):
    """Stand-in worker (module level: the pool pickles it by name)."""
    import signal
    from evoalgo import verifier as vmod
    if i == 1:
        os.kill(os.getpid(), signal.SIGKILL)
    return vmod._check_worker_chunk_real(ctx, i, *args)


def test_dead_worker_falls_back_to_the_serial_result(tmp_path, monkeypatch):
    """A verifier worker killed mid-run (as by the OOM killer) does not end the
    verification with BrokenProcessPool: the rest is checked serially, with
    the same result as a serial run."""
    from evoalgo import verifier as vmod

    monkeypatch.setattr(vmod, "_check_worker_chunk_real", vmod._worker_check_chunk, raising=False)
    monkeypatch.setattr(vmod, "_worker_check_chunk", _dies_on_chunk_1)  # forked workers inherit it
    for label, code in {"known-good": reference_code("dynamic_bfs"),
                        "fault": compose_fault_code("dynamic_bfs", real_faults("dynamic_bfs")[0])}.items():
        serial = _verify_tuple(_make_verifier("dynamic_bfs", 3, chunk_size=10, workers=1),
                               code, tmp_path, f"{label}_serial")
        parallel = _verify_tuple(_make_verifier("dynamic_bfs", 3, chunk_size=10, workers=2),
                                 code, tmp_path, f"{label}_parallel")
        assert serial == parallel, (label, serial, parallel)


def test_worker_count_fits_available_memory(monkeypatch):
    from evoalgo import verifier as vmod
    monkeypatch.setattr(vmod, "_available_memory_mb", lambda: 3 * vmod.WORKER_MEMORY_MB + 1)
    assert vmod._default_workers() == min(3, os.cpu_count() or 1)
    monkeypatch.setattr(vmod, "_available_memory_mb", lambda: 100)
    assert vmod._default_workers() == 1


def test_fault_counterexamples_trigger_invariant():
    """Fast (in-process): each real fault's documented counterexample violates
    the invariant, and each equivalent control does not. This re-checks the
    corpus metadata against the real check_invariant without the sandbox."""
    problems = {n: get_problem(n) for n in CORPUS_PROBLEMS}
    for fault in FAULTS:
        pname = fault["problem"]
        p = problems[pname]
        root = 0 if p.needs_root else None
        code = compose_fault_code(pname, fault)
        ns: dict = {}
        exec(compile(code, "<cand>", "exec"), ns)
        init, ins, dele = ns["init"], ns["insert_edge"], ns["delete_edge"]
        if fault["is_equivalent"]:
            # Spot-check the control is valid on a small universe.
            for g in (load_nauty_rooted_digraphs(3) if p.directed else _undirected(3)):
                gl = g.tolist()
                st = init(gl)
                assert p.check_invariant(st, g, root), fault["id"]
            continue
        n, gl = counterexample_graph(fault)
        if not p.directed:
            gl = [[gl[u][v] | gl[v][u] for v in range(n)] for u in range(n)]
        g = np.array(gl, dtype=int)
        st = init(gl)
        op = fault["counterexample"][2]
        if op == "init":
            assert not p.check_invariant(st, g, root), fault["id"]
        else:
            ot, (u, v) = op
            g2 = [row[:] for row in gl]
            bit = 1 if ot == "insert" else 0
            g2[u][v] = bit
            if not p.directed:
                g2[v][u] = bit
            st2 = (ins if ot == "insert" else dele)(g2, (u, v), st)
            assert not p.check_invariant(st2, np.array(g2, dtype=int), root), fault["id"]


def _undirected(n: int) -> list[np.ndarray]:
    """Every labelled undirected graph on n vertices."""
    import itertools
    pairs = list(itertools.combinations(range(n), 2))
    out = []
    for bits in itertools.product([0, 1], repeat=len(pairs)):
        g = np.zeros((n, n), dtype=int)
        for (u, v), b in zip(pairs, bits):
            g[u, v] = g[v, u] = b
        out.append(g)
    return out


def test_bfs_distance_field_is_certified():
    """BFS distances are part of the documented candidate state, so the
    checker must reject a candidate that keeps a valid parent tree but
    corrupts its distance field (previously invisible)."""
    p = get_problem("dynamic_bfs")
    g = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=int)
    gl = g.tolist()
    ns: dict = {}
    exec(compile(reference_code("dynamic_bfs"), "<cand>", "exec"), ns)
    st = ns["init"](gl)
    assert p.check_invariant(st, g, 0)
    bad = copy.deepcopy(st)
    bad["distances"] = {v: d + 2 for v, d in bad["distances"].items()}
    assert not p.check_invariant(bad, g, 0)
    # A state with no distance field falls back to parent-only (accepted).
    nodist = {"parent": st["parent"]}
    assert p.check_invariant(nodist, g, 0)


def test_fault_corpus_metadata_complete():
    """Each problem has its real faults (REAL_FAULTS) + 1 equivalent control,
    all with documented metadata; real faults carry an n<=5 counterexample."""
    for pname in CORPUS_PROBLEMS:
        faults = faults_for(pname)
        real = [f for f in faults if not f["is_equivalent"]]
        ctrl = [f for f in faults if f["is_equivalent"]]
        assert len(real) == REAL_FAULTS[pname], (pname, len(real))
        assert len(ctrl) == 1, (pname, len(ctrl))
        for f in faults:
            assert f["id"] and f["description"] and f["fault_class"]
            if not f["is_equivalent"]:
                n, edges, op = f["counterexample"]
                assert n <= 5, f["id"]
                if op != "init":
                    ot, (u, v) = op
                    assert ot in ("insert", "delete")


def test_yang_dfs_reference_and_mutations_in_process():
    """Fast (in-process): the Yang et al. reference keeps a valid DFS tree on
    every single update of every non-isomorphic rooted digraph with n <= 4
    and on random update sequences; each mutation's documented
    counterexample breaks it, and Y7 breaks over random sequences."""
    import random
    from evoalgo.selftest.references import YANG_DFS_CODE, YANG_DFS_MUTATIONS, yang_mutation_code
    p = get_problem("dynamic_dfs")

    def fns(code):
        ns: dict = {}
        exec(compile(code, "<yang>", "exec"), ns)
        return ns["init"], ns["insert_edge"], ns["delete_edge"]

    def apply(fs, gl, op, st):
        kind, (u, v) = op
        g2 = [row[:] for row in gl]
        g2[u][v] = 1 if kind == "insert" else 0
        st2 = (fs[1] if kind == "insert" else fs[2])(g2, (u, v), copy.deepcopy(st))
        return g2, st2

    def random_sequences_ok(fs, trials=400, seed=11):
        rng = random.Random(seed)
        for _ in range(trials):
            n = rng.choice([6, 8, 12])
            gl = [[int(i != j and rng.random() < 0.25) for j in range(n)] for i in range(n)]
            st = fs[0](gl)
            for _ in range(30):
                u, v = rng.sample(range(n), 2)
                gl, st = apply(fs, gl, ("delete" if gl[u][v] else "insert", (u, v)), st)
                if not p.check_invariant(st, np.array(gl), 0):
                    return False
        return True

    good = fns(YANG_DFS_CODE)
    for n in (2, 3, 4):
        for g in load_nauty_rooted_digraphs(n):
            gl = g.tolist()
            st = good[0](gl)
            assert p.check_invariant(st, g, 0)
            for u in range(n):
                for v in range(n):
                    if u != v:
                        g2, st2 = apply(good, gl, ("delete" if gl[u][v] else "insert", (u, v)), st)
                        assert p.check_invariant(st2, np.array(g2), 0), (gl, (u, v))
    assert random_sequences_ok(good)
    for m in YANG_DFS_MUTATIONS:
        bad = fns(yang_mutation_code(m))
        if m["counterexample"] is None:
            assert not random_sequences_ok(bad), m["id"]
            continue
        n, edges, op = m["counterexample"]
        gl = [[0] * n for _ in range(n)]
        for a, b in edges:
            gl[a][b] = 1
        g2, st2 = apply(bad, gl, op, bad[0](gl))
        assert not p.check_invariant(st2, np.array(g2), 0), m["id"]


@pytest.mark.slow
def test_yang_dfs_reference_passes_n5(tmp_path):
    """Completion signal of contribution 2: the engine validates Yang et al.
    dynamic DFS on the full n <= 5 universe."""
    from evoalgo.selftest.references import YANG_DFS_CODE
    cand = _verify_code("dynamic_dfs", YANG_DFS_CODE, 5, tmp_path)
    assert cand.state.value == "PASS", (cand.state.value, cand.failing_case)
