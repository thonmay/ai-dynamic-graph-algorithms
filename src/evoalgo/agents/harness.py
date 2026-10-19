"""Harness backends: an existing coding agent does the call with its own tools.

The harness is told the same role prompt and task text as the api backend,
plus the output path, and must leave the file on disk. Supported:

  enlcode / opencode   ``<bin> run [--agent A] --format json --dir RUN [-m MODEL] TASK``
  claude               ``claude -p --output-format json --permission-mode acceptEdits``
  codex                ``codex exec --json --sandbox workspace-write``

Only the enlcode path is exercised in this project; the others follow the
vendors' documented headless modes and are kept deliberately thin.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from .base import CallLog, CallResult, Task
from .prompts import system_prompt, task_message

ROLE_AGENT = {"generate": "generator_agent", "repair": "repairer_agent", "reflect": "reflector_agent"}


class HarnessBackend:
    name = "harness"

    def __init__(self, config: Any, run_dir: Path):
        self.config = config
        self.run_dir = Path(run_dir)
        self.log = CallLog(self.run_dir)
        self.timeout = config.agent_max_seconds

    def command(self, task: Task, prompt: str) -> list[str]:  # pragma: no cover - per harness
        raise NotImplementedError

    def parse(self, stdout: str) -> tuple[str | None, dict[str, int]]:
        return (stdout.strip()[-2000:] or None), {}

    def run(self, task: Task) -> CallResult:
        entry = self.log.new(self.name, task, self.config.model)
        task.output_path.parent.mkdir(parents=True, exist_ok=True)
        prompt = (f"{system_prompt(task.role)}\n\n---\n\n{task_message(task, False)}\n"
                  f"Write the file to exactly this path: {task.output_path}\n"
                  "You may not run the project's verifier or tests.")
        cmd = self.command(task, prompt)
        entry["command"] = cmd[:-1] + ["<task>"]
        started = time.monotonic()
        result = CallResult(ok=False)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout,
                                  cwd=self.run_dir)
            entry.update(returncode=proc.returncode, stderr=proc.stderr[-4000:])
            result.summary, result.usage = self.parse(proc.stdout)
            if proc.returncode != 0:
                result.error = f"exit {proc.returncode}: {proc.stderr[-500:]}"
        except FileNotFoundError:
            result.error = f"harness binary not found: {cmd[0]}"
        except subprocess.TimeoutExpired:
            result.error = f"harness timed out after {self.timeout}s"
        result.ok = task.output_path.is_file()
        entry.update(duration_s=round(time.monotonic() - started, 1), ok=result.ok,
                     error=result.error, summary=result.summary, usage=result.usage)
        self.log.write(entry)
        return result


class EnlcodeBackend(HarnessBackend):
    """enlcode (an opencode fork) or opencode itself: ``harness_bin`` picks the binary."""

    name = "enlcode"

    def __init__(self, config: Any, run_dir: Path):
        super().__init__(config, run_dir)
        self.bin = self.find_bin(config.harness_bin)

    @staticmethod
    def find_bin(override: str | None) -> str:
        return (override or os.environ.get("ENLCODE_PATH")
                or shutil.which("enlcode") or str(Path.home() / ".enlcode" / "enlcode"))

    def command(self, task: Task, prompt: str) -> list[str]:
        cmd = [self.bin, "run", "--format", "json", "--dir", str(self.run_dir)]
        agent = getattr(self.config, ROLE_AGENT[task.role], None)
        if agent:
            cmd += ["--agent", agent]
        if self.config.model:
            cmd += ["-m", self.config.model]
        return cmd + [prompt]

    def parse(self, stdout: str) -> tuple[str | None, dict[str, int]]:
        texts, usage = [], {"prompt_tokens": 0, "completion_tokens": 0}
        for line in stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict):
                continue
            part = ev.get("part") or {}
            if ev.get("type") == "text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
            elif ev.get("type") == "step_finish":
                tokens = part.get("tokens") or {}
                usage["prompt_tokens"] += int(tokens.get("input") or 0)
                usage["completion_tokens"] += int(tokens.get("output") or 0)
        return (texts[-1].strip() if texts else None), usage


class ClaudeBackend(HarnessBackend):
    name = "claude"

    def command(self, task: Task, prompt: str) -> list[str]:
        cmd = [self.config.harness_bin or "claude", "-p", "--output-format", "json",
               "--permission-mode", "acceptEdits", "--allowedTools", "Read,Write,Edit"]
        if self.config.model:
            cmd += ["--model", self.config.model]
        return cmd + [prompt]

    def parse(self, stdout: str) -> tuple[str | None, dict[str, int]]:
        try:
            d = json.loads(stdout)
        except json.JSONDecodeError:
            return super().parse(stdout)
        u = d.get("usage") or {}
        return d.get("result"), {"prompt_tokens": int(u.get("input_tokens") or 0),
                                 "completion_tokens": int(u.get("output_tokens") or 0)}


class CodexBackend(HarnessBackend):
    name = "codex"

    def command(self, task: Task, prompt: str) -> list[str]:
        cmd = [self.config.harness_bin or "codex", "exec", "--json", "--sandbox", "workspace-write",
               "--skip-git-repo-check", "-C", str(self.run_dir)]
        if self.config.model:
            cmd += ["-m", self.config.model]
        return cmd + [prompt]
