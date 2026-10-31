# AI-assisted code: generated and revised with Qwen3.8-Flash-Next and GLM-5.2
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Population management: selection, elitism, diversity, culling."""

from __future__ import annotations

import logging
import random
from typing import Any

from .candidate import Candidate, CandidateState

logger = logging.getLogger(__name__)


def _rank_key(candidate: Candidate) -> tuple:
    """Ranking key: smaller is better.

    Order: passing before failing, then higher fitness, then lower
    work_ratio. Passing-first separates correct candidates from failures
    robustly; work_ratio gives efficiency pressure among equally-correct
    candidates. Candidates without a measured work_ratio rank last among
    equals.
    """
    wr = candidate.work_ratio if candidate.work_ratio is not None else float("inf")
    return (0 if candidate.is_passing else 1, -candidate.fitness, wr)


def _rank_key_dict(candidate: dict) -> tuple:
    """Same ordering as _rank_key, over a serialized candidate dict.

    Used by the reporting path (export/status/history) which works on the
    JSON written by Candidate.to_json rather than live Candidate objects.
    """
    wr = candidate.get("work_ratio")
    wr = float("inf") if wr is None else wr
    passing = candidate.get("state") == "PASS"
    return (0 if passing else 1, -candidate.get("fitness", 0.0), wr)


class Population:
    """Manages the candidate collection for one run."""

    def __init__(
        self,
        max_size: int = 8,
        elitism_k: int = 2,
        diversity_threshold: float = 0.8,
        crossover_enabled: bool = False,
    ):
        self.max_size = max_size
        self.elitism_k = elitism_k
        self.diversity_threshold = diversity_threshold
        self.crossover_enabled = crossover_enabled
        self.candidates: list[Candidate] = []
        # Own generator: parent selection must not depend on other users of
        # the global `random` (e.g. HTTP retry jitter). Seeded by the orchestrator.
        self.rng = random.Random()

    def add(self, candidate: Candidate) -> None:
        self.candidates.append(candidate)

    @property
    def size(self) -> int:
        return len(self.candidates)

    @property
    def best_fitness(self) -> float:
        if not self.candidates:
            return 0.0
        return max(c.fitness for c in self.candidates)

    @property
    def best_candidate(self) -> Candidate | None:
        if not self.candidates:
            return None
        return min(self.candidates, key=_rank_key)

    @property
    def has_passing(self) -> bool:
        return any(c.is_passing for c in self.candidates)

    def select_parents(self, count: int = 1) -> list[Candidate | None]:
        """Select parents for offspring generation.

        Strategy:
        1. If no viable candidates, return [None] (fresh generation)
        2. Tournament selection: pick k=3 random viable candidates,
           return the fittest. This preserves selection pressure while
           ensuring different parents can be selected across repeated
           calls (the orchestrator calls this once per offspring).
        """
        if not self.candidates:
            return [None] * count

        # Rank best-first (passing, then fitness, then work_ratio)
        ranked = sorted(self.candidates, key=_rank_key)

        # Filter to candidates that produced some result (not NEW, not CRASH-only)
        viable = [c for c in ranked if c.state in (CandidateState.PASS, CandidateState.FAIL)]

        if not viable:
            return [None] * count

        if len(viable) == 1:
            return [viable[0]] * count

        parents: list[Candidate | None] = []
        tournament_k = min(3, len(viable))

        for _ in range(count):
            # Tournament: pick k random candidates, choose the best-ranked
            contenders = self.rng.sample(viable, tournament_k)
            best = min(contenders, key=_rank_key)
            parents.append(best)

        return parents

    def get_failed_repairable(self) -> list[Candidate]:
        """Return failed candidates that have reflections (eligible for repair)."""
        return [c for c in self.candidates if c.is_repairable]

    def compute_diversity(self) -> float:
        """Compute pairwise diversity of the population.

        Returns a value in [0, 1] where 1 means maximum diversity.
        Low diversity (high similarity) triggers the diversity injection.

        We use a simple metric: fraction of candidates with distinct
        (fitness, failing_case_signature) pairs.
        """
        if len(self.candidates) <= 1:
            return 1.0

        signatures = set()
        for c in self.candidates:
            sig = (
                round(c.fitness, 2),
                c.error_message[:50] if c.error_message else "",
                c.tests_passed,
            )
            signatures.add(sig)

        diversity = len(signatures) / len(self.candidates)
        return diversity

    @property
    def needs_diversity_injection(self) -> bool:
        """True if population similarity exceeds threshold."""
        return self.compute_diversity() < self.diversity_threshold

    def cull(self) -> list[Candidate]:
        """Reduce population to max_size, keeping best and most diverse.

        Returns the discarded candidates.
        """
        if len(self.candidates) <= self.max_size:
            return []

        # Rank best-first (passing, then fitness, then work_ratio)
        ranked = sorted(self.candidates, key=_rank_key)

        # Keep elite (top-k)
        elite = ranked[: self.elitism_k]

        # Fill remaining slots: passing candidates are always kept (ranked by
        # work_ratio); failing candidates are deduplicated by failure signature
        # so the population explores distinct failure modes rather than many
        # variants that break the same way.
        rest = ranked[self.elitism_k:]
        seen_signatures = set()
        kept_rest: list[Candidate] = []
        discarded: list[Candidate] = []

        for c in rest:
            if len(elite) + len(kept_rest) >= self.max_size:
                # Discard the rest
                c.transition(CandidateState.DISCARDED)
                discarded.append(c)
                continue

            if c.is_passing:
                kept_rest.append(c)
                continue

            sig = (
                round(c.fitness, 2),
                c.error_message[:50] if c.error_message else "",
            )
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                kept_rest.append(c)
            else:
                c.transition(CandidateState.DISCARDED)
                discarded.append(c)

        self.candidates = elite + kept_rest
        return discarded

    def to_json(self) -> list[dict[str, Any]]:
        return [c.to_json() for c in self.candidates]

    @classmethod
    def from_json(
        cls,
        data: list[dict[str, Any]],
        max_size: int = 8,
        elitism_k: int = 2,
        diversity_threshold: float = 0.8,
        crossover_enabled: bool = False,
    ) -> Population:
        pop = cls(
            max_size=max_size,
            elitism_k=elitism_k,
            diversity_threshold=diversity_threshold,
            crossover_enabled=crossover_enabled,
        )
        pop.candidates = [Candidate.from_json(c) for c in data]
        return pop
