# AI-assisted code: generated and revised with Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tests for the dynamic_lbfs problem definition (open-problem tier).

Covers the (LB) 4-point certificate:
  - the canonical oracle output passes check_invariant on all labeled
    undirected graphs n<=5;
  - for n<=5 the set of permutations accepted by check_invariant equals the
    set produced by brute-force LexBFS over all starts and tie-breaks;
  - the 4-cycle has exactly 8 accepted orderings;
  - non-permutations (wrong length, duplicates, out-of-range) are rejected;
  - an MCS ordering that is not a LexBFS ordering is rejected (found by
    search).
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from evoalgo.problem_definitions import DynamicLBFS, DynamicMCS


def all_undirected(n: int) -> list[list[list[int]]]:
    """Every labeled undirected graph on n vertices, as 0/1 matrices."""
    graphs = []
    for bits in itertools.product([0, 1], repeat=n * (n - 1) // 2):
        g = [[0] * n for _ in range(n)]
        k = 0
        for u in range(n):
            for v in range(u + 1, n):
                g[u][v] = g[v][u] = bits[k]
                k += 1
        graphs.append(g)
    return graphs


def lex_bfs_multi(graph, n: int, start: int, tiebreak: list[int]) -> list[int]:
    """Canonical multi-cell partition-refinement LexBFS.

    start: first vertex. tiebreak: total order used to order the initial cell
    and break ties. Matches the verified scratch implementation.
    """
    cell = [start] + [v for v in tiebreak if v != start]
    partition = [cell]
    order = []
    while len(order) < n:
        p = partition[0][0]
        order.append(p)
        neigh = {v for v in range(n) if graph[p][v] == 1}
        refined = []
        for part in partition:
            part = [v for v in part if v != p]
            if not part:
                continue
            a = [v for v in part if v in neigh]
            b = [v for v in part if v not in neigh]
            if a:
                refined.append(a)
            if b:
                refined.append(b)
        partition = refined
    return order


def all_lexbfs_outputs(graph, n: int) -> set[tuple[int, ...]]:
    """All LexBFS outputs over every start and every tie-break."""
    outs = set()
    for start in range(n):
        for tiebreak in itertools.permutations(range(n)):
            outs.add(tuple(lex_bfs_multi(graph, n, start, list(tiebreak))))
    return outs


def mcs_ordering(graph, n: int) -> list[int]:
    chosen = set()
    cardinality = {v: 0 for v in range(n)}
    ordering = []
    for _ in range(n):
        unchosen = [u for u in range(n) if u not in chosen]
        if not unchosen:
            break
        max_card = max(cardinality[u] for u in unchosen)
        candidates = [u for u in unchosen if cardinality[u] == max_card]
        v = min(candidates)
        ordering.append(v)
        chosen.add(v)
        for u in range(n):
            if graph[v][u] == 1 and u not in chosen:
                cardinality[u] += 1
    return ordering


@pytest.fixture(scope="module")
def lbfs() -> DynamicLBFS:
    return DynamicLBFS()


class TestOraclePasses:
    def test_oracle_output_satisfies_certificate(self, lbfs: DynamicLBFS):
        """The canonical oracle output passes check_invariant on all n<=5."""
        for n in (3, 4, 5):
            for g in all_undirected(n):
                mat = np.array(g, dtype=int)
                oracle = lbfs.offline_compute(mat, None)
                assert lbfs.check_invariant(oracle, mat, None), (
                    f"oracle {oracle} rejected on n={n} graph {g}"
                )

    def test_oracle_is_a_permutation(self, lbfs: DynamicLBFS):
        for n in (3, 4, 5):
            for g in all_undirected(n):
                mat = np.array(g, dtype=int)
                oracle = lbfs.offline_compute(mat, None)
                assert sorted(oracle) == list(range(n))


class TestBruteForceEquivalence:
    @pytest.mark.parametrize("n", [3, 4, 5])
    def test_accepted_equals_all_lexbfs_outputs(self, lbfs: DynamicLBFS, n: int):
        """Set of accepted perms == set of all LexBFS outputs, for all graphs."""
        for g in all_undirected(n):
            mat = np.array(g, dtype=int)
            accepted = {
                p for p in itertools.permutations(range(n))
                if lbfs.check_invariant(list(p), mat, None)
            }
            lexouts = all_lexbfs_outputs(g, n)
            assert accepted == lexouts, (
                f"n={n} graph {g}: |accepted|={len(accepted)} "
                f"|lexbfs|={len(lexouts)}; "
                f"only-accepted={accepted - lexouts}; "
                f"only-lexbfs={lexouts - accepted}"
            )


class TestFourCycle:
    def test_exactly_eight_accepted_orderings(self, lbfs: DynamicLBFS):
        # 4-cycle 0-1-2-3-0: edges (0,1),(1,2),(2,3),(3,0)
        cyc = [[0, 1, 0, 1],
               [1, 0, 1, 0],
               [0, 1, 0, 1],
               [1, 0, 1, 0]]
        mat = np.array(cyc, dtype=int)
        accepted = [
            p for p in itertools.permutations(range(4))
            if lbfs.check_invariant(list(p), mat, None)
        ]
        assert len(accepted) == 8
        # all 8 are genuine LexBFS outputs
        assert {p for p in accepted} == all_lexbfs_outputs(cyc, 4)


# a simple path 0-1-2-3 (n=4)
_PATH_MAT = np.array([[0, 1, 0, 0],
                      [1, 0, 1, 0],
                      [0, 1, 0, 1],
                      [0, 0, 1, 0]], dtype=int)


class TestNonPermutations:
    def test_wrong_length_rejected(self, lbfs: DynamicLBFS):
        assert not lbfs.check_invariant([0, 1, 2], _PATH_MAT, None)
        assert not lbfs.check_invariant([0, 1, 2, 3, 4], _PATH_MAT, None)

    def test_duplicates_rejected(self, lbfs: DynamicLBFS):
        assert not lbfs.check_invariant([0, 1, 1, 3], _PATH_MAT, None)

    def test_out_of_range_rejected(self, lbfs: DynamicLBFS):
        assert not lbfs.check_invariant([0, 1, 2, 9], _PATH_MAT, None)
        assert not lbfs.check_invariant([0, 1, 2, -1], _PATH_MAT, None)

    def test_missing_vertex_rejected(self, lbfs: DynamicLBFS):
        # length 4 but not a permutation of {0,1,2,3}
        assert not lbfs.check_invariant([0, 1, 2, 2], _PATH_MAT, None)

    def test_dict_state_form(self, lbfs: DynamicLBFS):
        # the documented state shape {"ordering": [...]} must work too
        good = lbfs.offline_compute(_PATH_MAT, None)
        assert lbfs.check_invariant({"ordering": good}, _PATH_MAT, None)
        assert not lbfs.check_invariant({"ordering": [0, 1, 1, 3]}, _PATH_MAT, None)


class TestMCSNotLexBFS:
    def test_find_and_reject(self, lbfs: DynamicLBFS):
        """Search for an MCS ordering that is not a LexBFS ordering."""
        found = None
        for n in (3, 4, 5):
            for g in all_undirected(n):
                mcs = mcs_ordering(g, n)
                # is it a LexBFS ordering? (membership in the all-outputs set)
                if tuple(mcs) not in all_lexbfs_outputs(g, n):
                    found = (n, g, mcs)
                    break
            if found:
                break
        assert found is not None, "expected an MCS-not-LexBFS counterexample n<=5"
        n, g, mcs = found
        mat = np.array(g, dtype=int)
        # sanity: it is a valid MCS ordering
        assert DynamicMCS().check_invariant(mcs, mat, None)
        # but it is rejected by the LexBFS certificate
        assert not lbfs.check_invariant(mcs, mat, None), (
            f"MCS ordering {mcs} on n={n} graph {g} was accepted as LexBFS"
        )
