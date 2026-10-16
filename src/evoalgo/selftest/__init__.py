"""Verifier self-test references and fault corpus.

This package holds the known-good reference candidates and the seeded-fault
corpus used by ``evoalgo verify`` (the FR-VER-08 self-test) and by
``tests/test_verifier_iso.py``.

- :mod:`evoalgo.selftest.references` -- the known-good dynamic BFS and DFS
  references (honestly labelled as validate-or-rebuild, Yang et al. Lemma-1
  informed), as self-contained candidate modules.
- :mod:`evoalgo.selftest.faults` -- the seeded-fault corpus: one-line
  mutations of the references, each with a documented minimal
  counterexample at n<=5, plus one equivalent control per problem (a valid
  algorithm variant the checker must accept, proving it is not tie-broken).
"""

from .references import reference_code, reference_functions, REFERENCE_CODE
from .faults import FAULTS, faults_for, compose_fault_code

__all__ = [
    "reference_code",
    "reference_functions",
    "REFERENCE_CODE",
    "FAULTS",
    "faults_for",
    "compose_fault_code",
]
