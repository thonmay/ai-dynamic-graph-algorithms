# AI-assisted code: generated and revised with GLM-5.2
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Reflector: wraps the LLM reflector agent.

The reflector reads a failed candidate and its failing case, invokes
the reflector agent, and stores the structured reflection.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .candidate import Candidate
from .llm_provider import LLMProvider
from .problem_definitions import ProblemDefinition

logger = logging.getLogger(__name__)


class Reflector:
    """Analyzes failed candidates and produces structured reflections."""

    def __init__(self, provider: LLMProvider, problem: ProblemDefinition):
        self.provider = provider
        self.problem = problem

    def reflect(
        self,
        candidate: Candidate,
        run_dir: Path | str,
        generation: int,
    ) -> str | None:
        """Produce a structured reflection for a failed candidate.

        Returns the reflection text, or None on failure.
        """
        run_dir = Path(run_dir)
        reflections_dir = run_dir / "reflections"
        reflections_dir.mkdir(parents=True, exist_ok=True)

        # Read the candidate's source code
        code_path = Path(candidate.code_path)
        if not code_path.is_absolute():
            code_path = run_dir / candidate.code_path

        try:
            failed_code = code_path.read_text()
        except Exception as e:
            logger.error("Cannot read candidate code for reflection: %s", e)
            return None

        # Build failing case info
        failing_case: dict[str, Any] = candidate.failing_case or {
            "error": candidate.error_message or "Unknown failure",
        }

        reflection_filename = f"{candidate.id}.md"
        reflection_path = reflections_dir / reflection_filename

        result = self.provider.reflect(
            problem_name=self.problem.name,
            failed_code=failed_code,
            failing_case=failing_case,
            reflection_filename=reflection_filename,
            workdir=str(run_dir),
        )

        if result is None:
            logger.warning("Reflection failed for %s", candidate.id)
            return None

        # The agent should have written the reflection file directly.
        # If not, write what we got.
        if not reflection_path.exists():
            reflection_path.write_text(result)

        candidate.reflection_path = str(reflection_path)
        logger.info("Reflection written for %s: %s", candidate.id, reflection_path)
        return result
