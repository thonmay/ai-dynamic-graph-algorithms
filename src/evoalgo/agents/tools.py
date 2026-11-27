# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tools the built-in agent loop executes on behalf of the model.

The model sees JSON schemas and returns tool calls; nothing here trusts its
arguments. Every path is resolved against a fixed allow-list:

  read_file       the run's candidates/ and reflections/, and the pack folder
  write_candidate / edit_candidate   only the single output file of this call
  run_examples    the public example set (see examples.py), never the
                  hidden verifier

Tool results are plain strings, truncated so a large file or failure dump
cannot flood the context.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import Task
from .examples import run_examples

MAX_RESULT_CHARS = 8000
MAX_FILE_CHARS = 60_000


def _clip(text: str, limit: int = MAX_RESULT_CHARS) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]}\n... [{len(text) - limit} characters omitted] ...\n{text[-half:]}"


def schemas(role: str) -> list[dict[str, Any]]:
    """OpenAI function-tool schemas for one role."""
    read = {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from candidates/, reflections/ or the problem pack folder "
                       "(e.g. 'candidates/gen001_c02.py', 'pack/brief.md').",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}},
                       "required": ["path"]}}}
    if role == "reflect":
        write = {"type": "function", "function": {
            "name": "write_reflection",
            "description": "Write the reflection (markdown with FAILURE_DESCRIPTION, ROOT_CAUSE, "
                           "REPAIR_HINTS sections). Replaces the whole file.",
            "parameters": {"type": "object", "properties": {"text": {"type": "string"}},
                           "required": ["text"]}}}
        return [read, write]
    write = {"type": "function", "function": {
        "name": "write_candidate",
        "description": "Write the complete candidate Python module. Replaces the whole file.",
        "parameters": {"type": "object", "properties": {"code": {"type": "string"}},
                       "required": ["code"]}}}
    edit = {"type": "function", "function": {
        "name": "edit_candidate",
        "description": "Replace one exact, unique snippet in the candidate file you already wrote.",
        "parameters": {"type": "object", "properties": {
            "old": {"type": "string", "description": "exact text, must occur exactly once"},
            "new": {"type": "string"}}, "required": ["old", "new"]}}}
    examples = {"type": "function", "function": {
        "name": "run_examples",
        "description": "Run the current candidate file on the small public example set and "
                       "return the verdict and the first failing case. The final grade uses a "
                       "larger hidden set.",
        "parameters": {"type": "object", "properties": {}}}}
    return [read, write, edit, examples]


class Toolbox:
    """Executes tool calls for one Task."""

    def __init__(self, task: Task, pack_dir: Path | None):
        self.task = task
        self.pack_dir = pack_dir.resolve() if pack_dir else None
        self.out = task.output_path
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.examples_runs = 0

    def _is_under_roots(self, path: Path, roots: list[Path | None]) -> bool:
        return any(r is not None and (path == r or r in path.parents) for r in roots)

    def _run_roots(self) -> list[Path]:
        run = self.task.run_dir.resolve()
        return [(run / "candidates").resolve(), (run / "reflections").resolve()]

    def _resolve_read(self, raw: str) -> Path | None:
        raw = (raw or "").strip().lstrip("/")
        if raw.startswith("pack/"):
            if self.pack_dir is None:
                return None
            base, rel = self.pack_dir, raw[len("pack/"):]
            allowed: list[Path | None] = [self.pack_dir]
        else:
            base, rel = self.task.run_dir.resolve(), raw
            allowed = list(self._run_roots())
        target = (base / rel).resolve()
        return target if self._is_under_roots(target, allowed) else None

    def _is_allowed_dir(self, folder: Path) -> bool:
        """True if folder is one of the readable roots or inside one."""
        return self._is_under_roots(folder.resolve(), [self.pack_dir, *self._run_roots()])

    def call(self, name: str, raw_args: str | None) -> str:
        try:
            args = json.loads(raw_args or "{}")
            if not isinstance(args, dict):
                raise ValueError("arguments must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            return f"error: invalid JSON arguments ({e})"
        try:
            handler = getattr(self, f"_t_{name}", None)
            if handler is None or name not in {s["function"]["name"] for s in schemas(self.task.role)}:
                return f"error: unknown tool {name!r}"
            return _clip(handler(**args))
        except TypeError as e:
            return f"error: bad arguments for {name}: {e}"

    def _t_read_file(self, path: str) -> str:
        target = self._resolve_read(path)
        if target is None:
            return "error: path not allowed; use candidates/..., reflections/... or pack/..."
        if not target.is_file():
            # List what exists so the model stops guessing file names.
            folder = target if target.is_dir() else target.parent
            if folder.is_dir() and self._is_allowed_dir(folder):
                prefix = str(path).rstrip("/") if target.is_dir() else str(path).rsplit("/", 1)[0]
                names = sorted(p.name for p in folder.iterdir() if p.is_file())[:30]
                return (f"error: no such file: {path}; files in {prefix}/: "
                        + (", ".join(names) or "(none)"))
            return f"error: no such file: {path}"
        return target.read_text(errors="replace")[:MAX_FILE_CHARS]

    def _t_write_candidate(self, code: str) -> str:
        if len(code) > MAX_FILE_CHARS:
            return f"error: candidate longer than {MAX_FILE_CHARS} characters"
        self.out.write_text(code)
        return f"wrote {self.out.relative_to(self.task.run_dir)} ({len(code.splitlines())} lines)"

    def _t_write_reflection(self, text: str) -> str:
        self.out.write_text(text[:MAX_FILE_CHARS])
        return f"wrote {self.out.relative_to(self.task.run_dir)}"

    def _t_edit_candidate(self, old: str, new: str) -> str:
        if not self.out.is_file():
            return "error: no candidate written yet; call write_candidate first"
        text = self.out.read_text()
        count = text.count(old) if old else 0
        if count != 1:
            return f"error: 'old' must occur exactly once in the candidate (found {count})"
        self.out.write_text(text.replace(old, new, 1))
        return "edited candidate"

    def _t_run_examples(self) -> str:
        if not self.out.is_file():
            return "error: no candidate written yet; call write_candidate first"
        self.examples_runs += 1
        report = run_examples(self.task.problem, self.out.read_text())
        return json.dumps(report, indent=1, default=str)
