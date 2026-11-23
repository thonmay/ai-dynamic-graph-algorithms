# AI-assisted code: generated and revised with Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Verifier self-test: known-good references (``references``) and the seeded-fault
corpus with equivalent controls (``faults``), used by ``evoalgo verify`` and the
tests.
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
