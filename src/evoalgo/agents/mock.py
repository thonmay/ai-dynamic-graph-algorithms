"""The ``mock`` backend: scripted, offline, deterministic.

For tests and demos. ``generate`` and ``repair`` write a known-good recompute
candidate for the run's problem (so a mock run always reaches fitness 1.0),
and ``reflect`` writes a fixed three-section reflection. Set ``mock_script``
in the config to a list of "good"/"bad"/"none" entries to script what each
successive candidate call produces.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import CallLog, CallResult, Task


class MockBackend:
    name = "mock"

    def __init__(self, config: Any, run_dir: Path):
        self.config = config
        self.log = CallLog(Path(run_dir))
        self.script = list(getattr(config, "mock_script", None) or [])
        self.calls = 0

    def run(self, task: Task) -> CallResult:
        from ..cli import _generate_known_bad_candidate, _generate_known_good_candidate

        entry = self.log.new(self.name, task, None)
        task.output_path.parent.mkdir(parents=True, exist_ok=True)
        if task.role == "reflect":
            task.output_path.write_text(
                "## FAILURE_DESCRIPTION\nscripted\n\n## ROOT_CAUSE\nscripted\n\n"
                "## REPAIR_HINTS\nrecompute from scratch\n")
            kind = "reflection"
        else:
            kind = self.script[self.calls] if self.calls < len(self.script) else "good"
            self.calls += 1
            if kind == "good":
                task.output_path.write_text(_generate_known_good_candidate(task.problem))
            elif kind == "bad":
                task.output_path.write_text(_generate_known_bad_candidate(task.problem))
        ok = task.output_path.is_file()
        entry.update(ok=ok, scripted=kind, task_chars=len(task.problem_prompt))
        self.log.write(entry)
        return CallResult(ok=ok, summary=f"mock {task.role}: {kind}")
