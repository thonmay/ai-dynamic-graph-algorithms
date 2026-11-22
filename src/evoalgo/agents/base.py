# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Backend interface shared by the orchestrator and every agent backend.

A backend performs one role call (generate, repair or reflect) and leaves its
product on disk:

  generate / repair  ->  <run>/candidates/<candidate_id>.py
  reflect            ->  <run>/reflections/<candidate_id>.md

The orchestrator only checks that the file exists; how it got there (tool
loop, harness, script) is the backend's business. Every call is logged to
<run>/prompt_logs/call_NNNN.json.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

@dataclass
class Task:
    """One role call. ``context`` holds the role-specific inputs."""

    role: str                      # generate | repair | reflect
    candidate_id: str              # file stem the call must produce
    problem: str                   # checker name, e.g. dynamic_bfs
    problem_prompt: str            # problem definition + brief + goal + hint
    run_dir: Path
    parent_code: str | None = None
    failed_code: str | None = None
    reflection: str | None = None
    failing_case: dict[str, Any] | None = None
    focus: str | None = None       # specialist agent's focus (dynamic agent generation)

    @property
    def output_path(self) -> Path:
        if self.role == "reflect":
            return self.run_dir / "reflections" / f"{self.candidate_id}.md"
        return self.run_dir / "candidates" / f"{self.candidate_id}.py"


@dataclass
class CallResult:
    ok: bool                       # the expected output file was written
    summary: str | None = None     # the agent's final message
    error: str | None = None
    usage: dict[str, int] = field(default_factory=dict)  # prompt/completion tokens
    steps: int = 0                 # model turns (api backend)
    tool_calls: list[str] = field(default_factory=list)


class Backend(Protocol):
    name: str

    def run(self, task: Task) -> CallResult: ...


class CallLog:
    """Writes one JSON file per call (FR-AGENT-05)."""

    def __init__(self, run_dir: Path):
        self.dir = Path(run_dir) / "prompt_logs"
        self.dir.mkdir(parents=True, exist_ok=True)
        existing = [int(p.stem.split("_")[1]) for p in self.dir.glob("call_*.json")
                    if p.stem.split("_")[1].isdigit()]
        self.count = max(existing, default=0)

    def write(self, entry: dict[str, Any]) -> None:
        path = self.dir / f"{entry['call_id']}.json"
        path.write_text(json.dumps(entry, indent=2, ensure_ascii=False, default=str))

    def new(self, backend: str, task: Task, model: str | None) -> dict[str, Any]:
        self.count += 1
        return {
            "call_id": f"call_{self.count:04d}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "backend": backend, "model": model, "type": task.role,
            "candidate_id": task.candidate_id,
        }


def make_backend(config: Any, run_dir: Path) -> Backend:
    """Build the backend named by ``config.provider``."""
    kind = config.provider
    if kind == "api":
        from .api import ApiBackend
        return ApiBackend(config, run_dir)
    if kind == "opencode":
        from .harness import OpencodeBackend
        return OpencodeBackend(config, run_dir)
    if kind == "mock":
        from .mock import MockBackend
        return MockBackend(config, run_dir)
    raise ValueError(f"unknown provider {kind!r}")
