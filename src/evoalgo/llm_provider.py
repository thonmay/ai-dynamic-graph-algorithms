"""LLM Provider: adapter for invoking enlcode role agents.

The provider calls enlcode in non-interactive mode:
  enlcode run --agent <agent_name> --format json --dir <workdir> "task message"

Three operations map to the three role agents:
  generate(problem, parent_code, workdir) -> candidate code
  repair(problem, failed_code, reflection, workdir) -> repaired code
  reflect(problem, failed_code, failing_case, workdir) -> reflection text

Each call logs the full prompt and response (FR-AGENT-05).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import textwrap
import time
from pathlib import Path
from typing import Any

from .config import RunConfig

logger = logging.getLogger(__name__)


class LLMProvider:
    """enlcode CLI adapter for LLM agent invocations."""

    def __init__(
        self,
        config: RunConfig,
        run_dir: Path | str,
        enlcode_path: str | None = None,
    ):
        self.config = config
        self.run_dir = Path(run_dir)
        self.enlcode = enlcode_path or os.environ.get(
            "ENLCODE_PATH", str(Path.home() / ".enlcode" / "enlcode")
        )
        self.log_dir = self.run_dir / "prompt_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.call_count = 0
        # Researcher hint set through the control channel; added to every task.
        self.hint: str | None = None

    def _build_problem_prompt(self, problem_name: str) -> str:
        """Build the problem definition section of the prompt."""
        from .problem_definitions import get_problem

        problem = get_problem(problem_name)
        directed = "directed" if problem.directed else "undirected"
        needs_root = "yes" if problem.needs_root else "no"

        prompt = textwrap.dedent(f"""
            PROBLEM: {problem.name}
            Graph mode: {directed}
            Needs root/source: {needs_root}
            Interface: init(graph), insert_edge(graph, edge, state), delete_edge(graph, edge, state)
            State is passed in and returned. No globals. No get_result().
            Graphs are 0/1 adjacency matrices (list of lists). Vertex ids are 0-based integers.
            A legal update flips exactly one matrix entry.
        """).strip()
        brief = self._pack_brief()
        if brief:
            prompt += f"\n\nRESEARCH BRIEF:\n{brief.strip()}"
        if self.hint:
            prompt += f"\n\nRESEARCHER HINT: {self.hint}"
        return prompt

    def _pack_brief(self) -> str | None:
        """Return the configured pack's brief.md text, or None.

        Loaded lazily and cached; a missing/invalid pack yields no brief
        rather than breaking prompt building (config.validate() already
        reports pack errors before a run starts).
        """
        if not getattr(self.config, "pack", None):
            return None
        if not hasattr(self, "_pack_brief_cache"):
            self._pack_brief_cache: tuple[str, str | None] = (
                self.config.pack, self._load_pack_brief(self.config.pack)
            )
        if self._pack_brief_cache[0] != self.config.pack:
            self._pack_brief_cache = (
                self.config.pack, self._load_pack_brief(self.config.pack)
            )
        return self._pack_brief_cache[1]

    @staticmethod
    def _load_pack_brief(pack_name_or_path: str) -> str | None:
        try:
            from .packs import resolve_pack
            return resolve_pack(pack_name_or_path).brief
        except Exception as e:
            logger.warning("Could not load pack brief for %r: %s", pack_name_or_path, e)
            return None

    def generate(
        self,
        problem_name: str,
        parent_code: str | None,
        candidate_filename: str,
        generation: int,
        workdir: Path | str,
    ) -> str | None:
        """Invoke the generator agent to produce a new candidate.

        Returns the path to the written candidate file, or None on failure.
        """
        problem_prompt = self._build_problem_prompt(problem_name)
        candidates_dir = Path(workdir) / "candidates"
        candidates_dir.mkdir(parents=True, exist_ok=True)
        file_path = candidates_dir / candidate_filename

        if parent_code:
            task = f"""{problem_prompt}

TASK: Generate a NEW candidate algorithm derived from the parent below.
Write your candidate to: {file_path}

PARENT CANDIDATE:
```python
{parent_code}
```

Load the dynamic-graph-algorithms skill first. Implement init/insert_edge/delete_edge exactly.
"""
        else:
            task = f"""{problem_prompt}

TASK: Generate a new candidate algorithm from scratch.
Write your candidate to: {file_path}

Load the dynamic-graph-algorithms skill first. Implement init/insert_edge/delete_edge exactly.
Start from the offline algorithm and make it dynamic (incremental or decremental or fully dynamic).
"""

        return self._invoke_agent(
            agent_name=self.config.generator_agent,
            task=task,
            workdir=workdir,
            call_type="generate",
            candidate_id=candidate_filename.replace(".py", ""),
        )

    def repair(
        self,
        problem_name: str,
        failed_code: str,
        reflection: str,
        candidate_filename: str,
        workdir: Path | str,
    ) -> str | None:
        """Invoke the repairer agent to fix a failed candidate.

        Returns the path to the repaired file, or None on failure.
        """
        problem_prompt = self._build_problem_prompt(problem_name)
        candidates_dir = Path(workdir) / "candidates"
        candidates_dir.mkdir(parents=True, exist_ok=True)
        file_path = candidates_dir / candidate_filename

        task = f"""{problem_prompt}

TASK: Repair the failed candidate below using the reflection.
Apply the SMALLEST fix that addresses the root cause. Do not rewrite from scratch.
Trace the algorithm on the failing case before editing.
Write your repaired candidate to: {file_path}

FAILED CANDIDATE:
```python
{failed_code}
```

REFLECTION (failure analysis):
{reflection}

Load the dynamic-graph-algorithms skill first.
"""

        return self._invoke_agent(
            agent_name=self.config.repairer_agent,
            task=task,
            workdir=workdir,
            call_type="repair",
            candidate_id=candidate_filename.replace(".py", ""),
        )

    def reflect(
        self,
        problem_name: str,
        failed_code: str,
        failing_case: dict[str, Any],
        reflection_filename: str,
        workdir: Path | str,
    ) -> str | None:
        """Invoke the reflector agent to analyze a failure.

        Returns the path to the reflection file, or None on failure.
        """
        problem_prompt = self._build_problem_prompt(problem_name)
        reflections_dir = Path(workdir) / "reflections"
        reflections_dir.mkdir(parents=True, exist_ok=True)
        file_path = reflections_dir / reflection_filename

        task = f"""{problem_prompt}

TASK: Analyze the failed candidate below. Trace the algorithm on the failing case.
Identify the root cause. Write a structured reflection with three sections:
  FAILURE_DESCRIPTION: <what went wrong>
  ROOT_CAUSE: <which invariant clause was violated and why>
  REPAIR_HINTS: <specific, actionable suggestions for the repairer>

Write your reflection to: {file_path}

FAILED CANDIDATE:
```python
{failed_code}
```

FAILING CASE:
{json.dumps(failing_case, indent=2)}

Load the dynamic-graph-algorithms skill first.
"""

        return self._invoke_agent(
            agent_name=self.config.reflector_agent,
            task=task,
            workdir=workdir,
            call_type="reflect",
            candidate_id=reflection_filename.replace(".md", ""),
        )

    def _invoke_agent(
        self,
        agent_name: str,
        task: str,
        workdir: Path | str,
        call_type: str,
        candidate_id: str,
    ) -> str | None:
        """Call enlcode run with the given agent and task."""
        self.call_count += 1

        log_entry = {
            "call_id": f"call_{self.call_count:04d}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent": agent_name,
            "type": call_type,
            "candidate_id": candidate_id,
            "task": task,
        }

        cmd = [
            self.enlcode, "run",
            "--agent", agent_name,
            "--format", "json",
            "--dir", str(workdir),
        ]
        if self.config.model:
            cmd.extend(["-m", self.config.model])

        cmd.append(task)

        logger.info("Invoking %s agent (call #%d) for %s", agent_name, self.call_count, candidate_id)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 min max per agent call
            )

            log_entry["returncode"] = proc.returncode
            log_entry["stdout"] = proc.stdout[:10000]  # cap log size
            log_entry["stderr"] = proc.stderr[:5000]

            self._write_log(log_entry)

            if proc.returncode != 0:
                logger.error("Agent %s failed (exit %d): %s",
                             agent_name, proc.returncode, proc.stderr[:500])
                return None

            # Parse JSON output to find the agent's text response
            response_text = self._extract_response(proc.stdout)
            log_entry["response"] = response_text[:5000] if response_text else None
            self._write_log(log_entry)

            return response_text

        except subprocess.TimeoutExpired:
            log_entry["error"] = "Agent call timed out (600s)"
            self._write_log(log_entry)
            logger.error("Agent %s timed out", agent_name)
            return None
        except Exception as e:
            log_entry["error"] = str(e)
            self._write_log(log_entry)
            logger.error("Agent %s exception: %s", agent_name, e)
            return None

    def _extract_response(self, stdout: str) -> str | None:
        """Extract the agent's text response from enlcode JSON output.

        enlcode run --format json outputs a stream of JSON events, one per line.
        Event types:
          {"type":"text", "part":{"text":"...", ...}}  - text content
          {"type":"tool_use", "part":{...}}             - tool call
          {"type":"step_finish", "part":{"reason":"stop"}} - step complete
          {"type":"step_start", ...}                     - step start

        We collect all text events and return the concatenated result.
        The final text event before a "stop" step_finish is the agent's summary.
        """
        if not stdout.strip():
            return None

        lines = stdout.strip().split("\n")
        text_parts: list[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    continue
                event_type = event.get("type", "")
                if event_type == "text":
                    part = event.get("part", {})
                    text = part.get("text", "")
                    if isinstance(text, str):
                        text_parts.append(text)
            except json.JSONDecodeError:
                # Non-JSON line; ignore (could be log output)
                continue

        if text_parts:
            return text_parts[-1].strip()
        return None

    def _write_log(self, entry: dict) -> None:
        """Write a prompt log entry (FR-AGENT-05)."""
        log_file = self.log_dir / f"{entry['call_id']}.json"
        with open(log_file, "w") as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
