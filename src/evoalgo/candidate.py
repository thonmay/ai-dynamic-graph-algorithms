"""Candidate state machine and serialization.

Implements the single state machine from the design doc:
  NEW -> TESTING -> {PASS, FAIL, CRASH} -> DISCARDED

timeout maps to FAIL with a timeout flag. Crash maps to CRASH.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict, fields as dc_fields
from enum import Enum
from pathlib import Path
from typing import Any


class CandidateState(str, Enum):
    NEW = "NEW"
    TESTING = "TESTING"
    PASS = "PASS"
    FAIL = "FAIL"
    CRASH = "CRASH"
    DISCARDED = "DISCARDED"

    @property
    def is_terminal(self) -> bool:
        return self in (CandidateState.PASS, CandidateState.FAIL,
                        CandidateState.CRASH, CandidateState.DISCARDED)


# Valid transitions: (from_state, to_state)
_TRANSITIONS = {
    (CandidateState.NEW, CandidateState.TESTING),
    (CandidateState.TESTING, CandidateState.PASS),
    (CandidateState.TESTING, CandidateState.FAIL),
    (CandidateState.TESTING, CandidateState.CRASH),
    (CandidateState.PASS, CandidateState.DISCARDED),
    (CandidateState.FAIL, CandidateState.DISCARDED),
    (CandidateState.CRASH, CandidateState.DISCARDED),
}


class TransitionError(Exception):
    pass


@dataclass
class Candidate:
    id: str
    code_path: str
    generation: int
    state: CandidateState = CandidateState.NEW
    fitness: float = 0.0
    work_ratio: float | None = None
    timeout: bool = False
    parent_ids: list[str] = field(default_factory=list)
    tests_passed: int = 0
    tests_total: int = 0
    error_message: str | None = None
    failing_case: dict[str, Any] | None = None
    reflection_path: str | None = None
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def transition(self, new_state: CandidateState) -> None:
        key = (self.state, new_state)
        if key not in _TRANSITIONS:
            raise TransitionError(
                f"Invalid transition: {self.state.value} -> {new_state.value}"
            )
        self.state = new_state

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = self.state.value
        return d

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Candidate:
        data = dict(data)
        data["state"] = CandidateState(data["state"])
        known = {f.name for f in dc_fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    @property
    def is_passing(self) -> bool:
        return self.state == CandidateState.PASS

    @property
    def is_failed(self) -> bool:
        return self.state in (CandidateState.FAIL, CandidateState.CRASH)

    @property
    def is_repairable(self) -> bool:
        """A failed candidate with a reflection is eligible for repair."""
        return self.state == CandidateState.FAIL and self.reflection_path is not None
