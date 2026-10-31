# AI-assisted code: generated and revised with GLM-5.2, Claude Opus 5.5 and Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""LLM provider: the orchestrator's single entry point to the agent layer.

It builds the problem prompt (problem definition, pack brief, research goal,
live researcher hint) and hands each role call to the configured backend
(``evoalgo.agents``):

  generate(problem, parent_code, candidate_filename, generation, workdir)
  repair(problem, failed_code, reflection, candidate_filename, workdir)
  reflect(problem, failed_code, failing_case, reflection_filename, workdir)

Each returns the agent's final message, or None when no output file was
produced. ``call_count`` counts model calls for the run budget.
"""

from __future__ import annotations

import logging
import textwrap
from pathlib import Path
from typing import Any

from .agents import make_backend
from .agents.base import CallResult, Task
from .config import RunConfig

logger = logging.getLogger(__name__)


class LLMProvider:
    """Prompt building plus dispatch to the configured agent backend."""

    def __init__(self, config: RunConfig, run_dir: Path | str, backend: Any = None):
        self.config = config
        self.run_dir = Path(run_dir)
        (self.run_dir / "prompt_logs").mkdir(parents=True, exist_ok=True)
        self.backend = backend
        self.call_count = 0
        self.last_result: CallResult | None = None
        # Researcher hint set through the control channel; added to every task.
        self.hint: str | None = None

    def _backend(self) -> Any:
        if self.backend is None:
            self.backend = make_backend(self.config, self.run_dir)
        return self.backend

    def _build_problem_prompt(self, problem_name: str) -> str:
        """Build the problem definition section of the prompt."""
        from .problem_definitions import get_problem

        problem = get_problem(problem_name)
        directed = "directed" if problem.directed else "undirected"
        needs_root = "yes (vertex 0)" if problem.needs_root else "no"

        prompt = textwrap.dedent(f"""
            PROBLEM: {problem.name}
            Graph mode: {directed}
            Needs root/source: {needs_root}
            Interface: init(graph), insert_edge(graph, edge, state), delete_edge(graph, edge, state)
            State is passed in and returned. No globals. No get_result().
            Graphs are 0/1 adjacency matrices (list of lists). Vertex ids are 0-based integers.
            A legal update flips exactly one matrix entry.
        """).strip()
        if problem.STATE_CONTRACT:
            prompt += f"\n\nSTATE CONTRACT (what the verifier reads):\n{problem.STATE_CONTRACT}"
        brief = self._pack_brief()
        if brief:
            prompt += f"\n\nRESEARCH BRIEF:\n{brief.strip()}"
        goal = (getattr(self.config, "research_goal", None) or "").strip()
        if goal:
            prompt += f"\n\nRESEARCH GOAL FOR THIS RUN: {goal}"
        if self.hint:
            prompt += f"\n\nRESEARCHER HINT: {self.hint}"
        return prompt

    def _pack_brief(self) -> str | None:
        """The configured pack's brief.md text, or None (cached per pack)."""
        pack = getattr(self.config, "pack", None)
        if not pack:
            return None
        cache = getattr(self, "_pack_brief_cache", None)
        if cache is None or cache[0] != pack:
            self._pack_brief_cache = (pack, self._load_pack_brief(pack))
        return self._pack_brief_cache[1]

    @staticmethod
    def _load_pack_brief(pack_name_or_path: str) -> str | None:
        try:
            from .packs import resolve_pack
            return resolve_pack(pack_name_or_path).brief
        except Exception as e:
            logger.warning("Could not load pack brief for %r: %s", pack_name_or_path, e)
            return None

    def _call(self, task: Task) -> str | None:
        self.call_count += 1
        logger.info("Agent call #%d: %s %s via %s", self.call_count, task.role, task.candidate_id,
                    self.config.provider)
        result = self._backend().run(task)
        self.last_result = result
        if result.error:
            logger.warning("%s %s: %s", task.role, task.candidate_id, result.error)
        return (result.summary or "done") if result.ok else None

    def generate(self, problem_name: str, parent_code: str | None, candidate_filename: str,
                 generation: int, workdir: Path | str, focus: str | None = None) -> str | None:
        return self._call(Task(
            role="generate", candidate_id=Path(candidate_filename).stem, problem=problem_name,
            problem_prompt=self._build_problem_prompt(problem_name), run_dir=Path(workdir),
            parent_code=parent_code, focus=focus))

    def repair(self, problem_name: str, failed_code: str, reflection: str,
               candidate_filename: str, workdir: Path | str) -> str | None:
        return self._call(Task(
            role="repair", candidate_id=Path(candidate_filename).stem, problem=problem_name,
            problem_prompt=self._build_problem_prompt(problem_name), run_dir=Path(workdir),
            failed_code=failed_code, reflection=reflection))

    def reflect(self, problem_name: str, failed_code: str, failing_case: dict[str, Any],
                reflection_filename: str, workdir: Path | str) -> str | None:
        return self._call(Task(
            role="reflect", candidate_id=Path(reflection_filename).stem, problem=problem_name,
            problem_prompt=self._build_problem_prompt(problem_name), run_dir=Path(workdir),
            failed_code=failed_code, failing_case=failing_case))
