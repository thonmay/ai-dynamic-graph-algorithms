# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Role prompts (markdown files next to this module) and per-call task text.

The prompts are harness-neutral; the same text is used by the built-in api
backend and exported for coding-agent harnesses (see evoalgo.export).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..base import Task

PROMPT_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def system_prompt(role: str) -> str:
    return (PROMPT_DIR / f"{role}.md").read_text()


def task_message(task: Task, has_pack: bool) -> str:
    """The user message for one call: problem, inputs, and where to write."""
    out = task.output_path.relative_to(task.run_dir)
    parts = [task.problem_prompt, ""]
    if task.role == "generate":
        if task.parent_code:
            parts += ["TASK: derive a NEW candidate from the parent below.",
                      f"Output file: {out}", "", "PARENT CANDIDATE:", _code(task.parent_code)]
        else:
            parts += ["TASK: write a new candidate from scratch (start from the offline "
                      "algorithm and make it dynamic).", f"Output file: {out}"]
    elif task.role == "repair":
        parts += ["TASK: repair the failed candidate below using the reflection.",
                  f"Output file: {out}", "", "FAILED CANDIDATE:", _code(task.failed_code or ""),
                  "", "REFLECTION:", (task.reflection or "(none)").strip()]
    elif task.role == "reflect":
        parts += ["TASK: write a reflection for the failed candidate below.",
                  f"Output file: {out}", "", "FAILED CANDIDATE:", _code(task.failed_code or ""),
                  "", "FAILING CASE:", json.dumps(task.failing_case or {}, indent=2, default=str)]
    if task.focus:
        parts += ["", "SPECIALIST FOCUS:", task.focus.strip()]
    if has_pack:
        parts += ["", "More context: read_file('pack/brief.md') has the full research brief."]
    return "\n".join(parts).strip() + "\n"


def _code(code: str) -> str:
    return f"```python\n{code.rstrip()}\n```"
