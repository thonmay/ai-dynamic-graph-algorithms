# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Public examples: the small check an agent may run on its own candidate.

The full verifier (all non-isomorphic graphs up to the run bound, n <= 5 by
default) is the held-out grade and is never exposed to agents. This module
runs the same certificate checks on a small fixed public set, so an agent can
catch obvious bugs before the orchestrator grades the candidate:

  every non-isomorphic graph with 2 <= n <= ``PUBLIC_N_MAX`` (rooted classes
  for rooted problems), each with every single-edge flip.

The returned report never contains more than the first failing case.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from ..candidate import Candidate
from ..problem_definitions import get_problem
from ..sandbox import Sandbox
from ..verifier import Verifier

PUBLIC_N_MAX = 3
PUBLIC_TIMEOUT_SECONDS = 20


def run_examples(problem_name: str, code: str) -> dict[str, Any]:
    """Run ``code`` on the public example set; return a compact report."""
    problem = get_problem(problem_name)
    verifier = Verifier(
        problem=problem,
        sandbox=Sandbox(timeout_seconds=PUBLIC_TIMEOUT_SECONDS, directed=problem.directed),
        bound_n_max=PUBLIC_N_MAX, bound_n_random=0, bound_seq_len_max=1, bound_seq_count=0,
        bound_seed=0, relabels_per_class=0, use_offline=False, workers=1,
    )
    with tempfile.TemporaryDirectory(prefix="evoalgo-ex-") as tmp:
        path = Path(tmp) / "candidate.py"
        path.write_text(code)
        result = verifier.verify(Candidate(id="example", code_path=str(path), generation=0))
    report: dict[str, Any] = {
        "verdict": result.state.value,
        "passed": result.tests_passed,
        "total": result.tests_total,
        "scope": f"public examples: all non-isomorphic graphs with n <= {PUBLIC_N_MAX}, "
                 "every single-edge flip (the real grade uses a larger hidden set)",
    }
    if result.failing_case:
        report["first_failure"] = result.failing_case
    if result.error_message:
        report["error"] = result.error_message[:2000]
    if result.timeout:
        report["timeout"] = True
    return report
