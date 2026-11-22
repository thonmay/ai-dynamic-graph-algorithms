# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""The ``api`` backend: a small agent loop over any OpenAI-compatible endpoint.

The model only ever returns text or tool calls; this loop executes the calls
through ``Toolbox`` (path-confined, see tools.py), feeds the results back and
stops when the model answers without a tool call or a limit is hit.

Works with OpenRouter, OpenAI, vLLM, llama.cpp or Ollama: anything
that speaks ``/chat/completions`` with ``tools``. Connection settings come from
the run config (``api_base_url``, ``api_key_env``, ``api_ca_cert``,
``model``); the key itself is read from the environment, never stored.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from .base import CallLog, CallResult, Task
from .prompts import system_prompt, task_message
from .tools import Toolbox, schemas

logger = logging.getLogger(__name__)

TRUNCATED_NUDGE = ("Your last reply hit the output limit before any tool call. "
                   "Do not explain at length: call write_candidate (or write_reflection) now.")

# Known endpoints, so a config can say ``api_base_url: openrouter``.
ENDPOINTS = {
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
}


def _read_key(key_env: str) -> str | None:
    """The API key from the environment; the value is never logged."""
    return os.environ.get(key_env) or None


def _safe_error(e: Exception) -> str:
    """An error description for logs and the (committed) call log.

    Auth errors (401/403/407) carry a response body in which some providers
    echo part of the key, so for those only the type, status and the
    provider's error code are kept. Other errors keep their message (e.g. a
    400 for an over-long context).
    """
    status = getattr(e, "status_code", None)
    if status is None or status not in (401, 403, 407):
        return f"{type(e).__name__}: {e}"[:1000]
    body = getattr(e, "body", None)
    code = body.get("code") or body.get("type") if isinstance(body, dict) else None
    return f"{type(e).__name__} (HTTP {status}{f', {code}' if isinstance(code, str) else ''})"


class ApiBackend:
    name = "api"

    def __init__(self, config: Any, run_dir: Path, client: Any = None):
        self.config = config
        self.run_dir = Path(run_dir)
        self.log = CallLog(self.run_dir)
        self.max_steps = config.agent_max_steps
        self.max_seconds = config.agent_max_seconds
        self.temperature = config.agent_temperature
        self.model = config.model
        self._injected = client  # tests
        self._client: Any = None
        self._key: str | None = None

    # -- connection ---------------------------------------------------------

    def _connect(self) -> Any:
        """A client with the current key; rebuilt when the key changes."""
        if self._injected is not None:
            return self._injected
        import httpx
        from openai import OpenAI

        base, key_env = self.config.api_base_url, self.config.api_key_env
        if base in ENDPOINTS:
            base, default_env = ENDPOINTS[base]
            key_env = key_env or default_env
        if not base:
            raise RuntimeError("api_base_url is not set (e.g. 'openrouter' or a URL)")
        key = _read_key(key_env) if key_env else None
        if not key:
            raise RuntimeError(f"API key not found: export {key_env or 'the key variable'}")
        if self._client is not None and key == self._key:
            return self._client
        verify: Any = self.config.api_ca_cert or True
        self._key = key
        self._client = OpenAI(
            base_url=base, api_key=key, max_retries=3,
            http_client=httpx.Client(verify=verify, timeout=self.config.agent_request_timeout),
        )
        return self._client

    # -- one role call ------------------------------------------------------

    def run(self, task: Task) -> CallResult:
        entry = self.log.new(self.name, task, self.model)
        pack_dir = self._pack_dir()
        toolbox = Toolbox(task, pack_dir)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt(task.role)},
            {"role": "user", "content": task_message(task, pack_dir is not None)},
        ]
        entry["messages_start"] = messages[:]
        result = CallResult(ok=False)
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        started = time.monotonic()
        length_hits = 0
        try:
            client = self._connect()
            for step in range(1, self.max_steps + 1):
                if time.monotonic() - started > self.max_seconds:
                    result.error = f"time limit ({self.max_seconds}s) reached"
                    break
                if step > 1:
                    client = self._connect()  # pick up a changed key
                remaining = self.max_steps - step
                if remaining == 1 and not task.output_path.is_file():
                    messages.append({"role": "user", "content":
                                     "One turn left: write the output file now with your best version."})
                resp = self._complete(client, messages, task.role)
                result.steps = step
                if resp.usage:  # every turn costs tokens, including truncated ones
                    usage["prompt_tokens"] += resp.usage.prompt_tokens or 0
                    usage["completion_tokens"] += resp.usage.completion_tokens or 0
                if resp.choices[0].finish_reason == "length" and not resp.choices[0].message.tool_calls:
                    length_hits += 1
                    messages.append(_assistant_message(resp.choices[0].message, []))
                    messages.append({"role": "user", "content": TRUNCATED_NUDGE})
                    if length_hits >= 2:
                        result.error = "model output hit max_tokens twice without a tool call"
                        break
                    continue
                msg = resp.choices[0].message
                calls = list(msg.tool_calls or [])
                messages.append(_assistant_message(msg, calls))
                if not calls:
                    result.summary = (msg.content or "").strip() or None
                    break
                for tc in calls:
                    out = toolbox.call(tc.function.name, tc.function.arguments)
                    result.tool_calls.append(tc.function.name)
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": out})
            else:
                result.error = f"step limit ({self.max_steps}) reached"
        except Exception as e:  # network, auth, malformed response: one failed call, not a failed run
            result.error = _safe_error(e)
            logger.error("api backend call failed: %s", result.error)
        result.ok = task.output_path.is_file()
        result.usage = usage
        entry.update(
            duration_s=round(time.monotonic() - started, 1), steps=result.steps,
            tool_calls=result.tool_calls, examples_runs=toolbox.examples_runs,
            usage=usage, ok=result.ok, error=result.error, summary=result.summary,
            messages=_compact(messages),
        )
        self.log.write(entry)
        return result

    def _complete(self, client: Any, messages: list[dict[str, Any]], role: str) -> Any:
        """One chat turn."""
        return client.chat.completions.create(
            model=self.model, messages=messages, tools=schemas(role),
            tool_choice="auto", temperature=self.temperature,
            max_tokens=self.config.agent_max_tokens, **self._extra())

    def _extra(self) -> dict[str, Any]:
        """Per-request extras: reasoning off by default for tool-loop turns."""
        body = dict(self.config.api_extra_body or {})
        if self.config.agent_thinking is False:
            # vLLM/SGLang chat templates (Qwen3, GLM, ...) read this; others ignore it.
            body.setdefault("chat_template_kwargs", {}).setdefault("enable_thinking", False)
        return {"extra_body": body} if body else {}

    def _pack_dir(self) -> Path | None:
        if not getattr(self.config, "pack", None):
            return None
        try:
            from ..packs import resolve_pack
            return resolve_pack(self.config.pack).path
        except Exception:
            return None


def _assistant_message(msg: Any, calls: list[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
    if calls:
        out["tool_calls"] = [{"id": tc.id, "type": "function",
                              "function": {"name": tc.function.name,
                                           "arguments": tc.function.arguments or "{}"}}
                             for tc in calls]
    return out


def _compact(messages: list[dict[str, Any]], limit: int = 4000) -> list[dict[str, Any]]:
    """Trim long message bodies for the call log."""
    out = []
    for m in messages:
        m = dict(m)
        if isinstance(m.get("content"), str) and len(m["content"]) > limit:
            m["content"] = m["content"][:limit] + f" ...[{len(m['content']) - limit} chars]"
        if "tool_calls" in m:
            m["tool_calls"] = [json.loads(json.dumps(tc)) for tc in m["tool_calls"]]
            for tc in m["tool_calls"]:
                a = tc["function"]["arguments"]
                if len(a) > limit:
                    tc["function"]["arguments"] = a[:limit] + f" ...[{len(a) - limit} chars]"
        out.append(m)
    return out
