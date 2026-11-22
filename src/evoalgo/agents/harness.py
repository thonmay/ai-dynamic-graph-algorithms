# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Harness backend: an existing coding agent does the call with its own tools.

The harness is told the same role prompt and task text as the api backend,
plus the output path, and must leave the file on disk. The supported harness
is opencode: ``<bin> run [--agent A] --format json --dir RUN [-m MODEL] TASK``.
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

# Environment a coding-agent harness gets: an allow-list, so the API keys and
# passwords of unrelated tools in the user's shell are not handed to the agent
# (whose tool outputs are recorded) or to the model provider. Each harness
# also gets the variables it needs for its own model access.
BASE_ENV = ("HOME", "USER", "LOGNAME", "PATH", "SHELL", "TERM", "LANG", "TZ", "TMPDIR",
            "LD_LIBRARY_PATH", "NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "SSL_CERT_DIR",
            "REQUESTS_CA_BUNDLE", "http_proxy", "https_proxy", "no_proxy",
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "CURL_CA_BUNDLE", "NODE_OPTIONS",
            "ELAN_HOME", "LEAN_PROJECT", "EVOALGO_SANDBOX")
BASE_ENV_PREFIXES = ("LC_", "XDG_")
# Per harness: (names, prefixes) it needs for its own model access.
HARNESS_ENV = {
    # opencode keeps its provider credentials in its own config directory.
    "opencode": (("OPENCODE_PATH",), ("OPENCODE_",)),
}


def harness_env(harness: str, **overrides: str) -> dict[str, str]:
    """The allow-listed environment for ``harness`` plus ``overrides``."""
    names, prefixes = HARNESS_ENV.get(harness, ((), ()))
    keep, prefixes = set(BASE_ENV) | set(names), BASE_ENV_PREFIXES + prefixes
    env = {k: v for k, v in os.environ.items() if k in keep or k.startswith(prefixes)}
    return env | overrides


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
                                  cwd=self.run_dir, env=harness_env(self.name))
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


class OpencodeBackend(HarnessBackend):
    """opencode, driven headlessly; ``harness_bin`` overrides the binary."""

    name = "opencode"

    def __init__(self, config: Any, run_dir: Path):
        super().__init__(config, run_dir)
        self.bin = self.find_bin(config.harness_bin)

    @staticmethod
    def find_bin(override: str | None) -> str:
        return override or os.environ.get("OPENCODE_PATH") or shutil.which("opencode") or "opencode"

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

