# AI-assisted code: generated and revised with Qwen3.8-Flash-Next
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tests for Population selection/ranking (efficiency pressure).

Regression coverage for the bug where selection ranked by fitness only, so
among equally-correct candidates the oldest (insertion order) always won and
faster mutations were discarded. Also covers the cull dedup that collapsed all
passing candidates into one "duplicate" signature, and the timed-out-FAIL
edge case (fitness 1.0 but not passing).
"""

import pytest

from evoalgo.candidate import Candidate, CandidateState
from evoalgo.population import Population, _rank_key


def mk(cid, fitness, work_ratio, state=CandidateState.PASS, error_message=None):
    c = Candidate(id=cid, code_path=f"/tmp/{cid}.py", generation=1, parent_ids=[])
    c.fitness = fitness
    c.work_ratio = work_ratio
    c.state = state
    c.error_message = error_message
    return c


class TestRankKey:
    def test_passing_beats_failing_even_at_equal_fitness(self):
        # A timed-out FAIL can report fitness 1.0; a real PASS must still rank first.
        p = mk("pass", 1.0, 0.5)
        f = mk("fail", 1.0, 0.1, state=CandidateState.FAIL)
        assert _rank_key(p) < _rank_key(f)

    def test_lower_work_ratio_wins_among_passers(self):
        fast = mk("fast", 1.0, 0.2)
        slow = mk("slow", 1.0, 0.9)
        assert _rank_key(fast) < _rank_key(slow)

    def test_higher_fitness_wins_over_lower_regardless_of_work_ratio(self):
        good = mk("g", 1.0, 0.9)
        bad = mk("b", 0.5, 0.1)
        assert _rank_key(good) < _rank_key(bad)

    def test_none_work_ratio_ranks_last_among_equal_fitness(self):
        measured = mk("m", 1.0, 0.99)
        unmeasured = mk("u", 1.0, None)
        assert _rank_key(measured) < _rank_key(unmeasured)


class TestBestCandidate:
    def test_picks_fastest_passer_not_first_added(self):
        pop = Population(max_size=5, elitism_k=1)
        pop.add(mk("slow", 1.0, 0.9))
        pop.add(mk("fast", 1.0, 0.2))
        assert pop.best_candidate.id == "fast"

    def test_picks_passer_over_timed_out_fail(self):
        pop = Population(max_size=5, elitism_k=1)
        pop.add(mk("timeout", 1.0, 0.1, state=CandidateState.FAIL))
        pop.add(mk("real", 1.0, 0.5))
        assert pop.best_candidate.id == "real"

    def test_empty_population(self):
        assert Population().best_candidate is None


class TestCull:
    def test_keeps_lowest_work_ratio_passers(self):
        pop = Population(max_size=3, elitism_k=1)
        for cid, wr in [("slow", 0.9), ("best", 0.2), ("mid", 0.35), ("best2", 0.22)]:
            pop.add(mk(cid, 1.0, wr))
        pop.cull()
        kept = {c.id for c in pop.candidates}
        assert kept == {"best", "best2", "mid"}  # 3 lowest work ratios
        assert "slow" not in kept

    def test_does_not_discard_passers_as_duplicates(self):
        # Regression: all passers share signature (1.0, ""); previously only
        # one survived past the elite slot.
        pop = Population(max_size=3, elitism_k=1)
        for i in range(4):
            pop.add(mk(f"c{i}", 1.0, 0.1 * (i + 1)))
        pop.cull()
        assert len(pop.candidates) == 3
        assert all(c.is_passing for c in pop.candidates)

    def test_still_dedups_failures_with_same_signature(self):
        # Failures breaking the same way should still collapse to one.
        pop = Population(max_size=3, elitism_k=1)
        pop.add(mk("p", 1.0, 0.5))  # elite
        pop.add(mk("f1", 0.5, None, state=CandidateState.FAIL, error_message="boom at step 3"))
        pop.add(mk("f2", 0.5, None, state=CandidateState.FAIL, error_message="boom at step 3"))
        pop.add(mk("f3", 0.5, None, state=CandidateState.FAIL, error_message="crash parsing edge"))
        pop.cull()
        kept = {c.id for c in pop.candidates}
        assert "p" in kept
        assert ("f1" in kept) ^ ("f2" in kept)  # exactly one of the identical pair
        assert "f3" in kept  # distinct failure mode kept

    def test_noop_when_within_max_size(self):
        pop = Population(max_size=5, elitism_k=1)
        pop.add(mk("a", 1.0, 0.5))
        assert pop.cull() == []


class TestSelectParents:
    def test_tournament_prefers_lower_work_ratio(self):
        pop = Population(max_size=5, elitism_k=1)
        pop.add(mk("slow", 1.0, 0.9))
        pop.add(mk("fast", 1.0, 0.2))
        parents = pop.select_parents(count=50)
        # fast is strictly better; tournament should pick it nearly always
        assert sum(1 for p in parents if p.id == "fast") >= 45

    def test_empty_returns_none(self):
        assert Population().select_parents(3) == [None, None, None]
