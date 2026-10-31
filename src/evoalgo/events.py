# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Run event log and control channel.

Two append-only JSON Lines files in the run directory connect the engine to
any UI (web, CLI) without either importing the other:

  events.jsonl   written by the engine; one event per line, ``seq`` increases
                 by one per event. Live monitoring and replay both read it.
  control.jsonl  written by a UI or ``evoalgo control``; one command per line.
                 The engine reads it at generation boundaries and answers
                 every command with a ``control_ack`` or ``control_reject``
                 event, so the event log alone records how a run was steered.

Only complete lines (terminated by a newline) are read, so a reader never
sees a half-written record.
"""

from __future__ import annotations

import json
import os
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

EVENTS_FILE = "events.jsonl"
CONTROL_FILE = "control.jsonl"
# Written by a running engine ({pid, host, started}), removed when it exits.
ENGINE_FILE = "engine.json"
# A harness run with no check for this long counts as abandoned. A --final
# check on a directed problem takes ~12 min, so this stays well above it.
HARNESS_IDLE_SECONDS = 2 * 3600

# Commands a UI may send. "set" changes one steerable field.
COMMANDS = {"pause", "resume", "stop", "hint", "set"}
# field -> (type, min, max)
STEERABLE_FIELDS: dict[str, tuple[type, int, int]] = {
    "model_call_budget": (int, 1, 100_000),
    "population_size": (int, 1, 50),
}
MAX_HINT_CHARS = 2000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _read_complete_lines(path: Path) -> Iterator[dict[str, Any]]:
    """Yield parsed JSON objects from complete lines; skip malformed ones."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return
    end = data.rfind(b"\n")
    if end < 0:
        return
    for raw in data[: end + 1].splitlines():
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            yield obj


def _append_line(path: Path, obj: dict[str, Any]) -> None:
    line = json.dumps(obj, ensure_ascii=False, default=str) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def read_events(run_dir: Path | str, since: int = 0) -> list[dict[str, Any]]:
    """Return events with ``seq >= since`` in file order."""
    return [e for e in _read_complete_lines(Path(run_dir) / EVENTS_FILE)
            if e.get("seq", -1) >= since]


class EventLog:
    """Append-only writer for ``events.jsonl``."""

    def __init__(self, run_dir: Path | str):
        self.path = Path(run_dir) / EVENTS_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = list(_read_complete_lines(self.path))
        self.next_seq = (max(e.get("seq", -1) for e in existing) + 1) if existing else 0

    def emit(self, type_: str, **data: Any) -> dict[str, Any]:
        event = {"seq": self.next_seq, "ts": data.pop("ts", None) or _now(), "type": type_, **data}
        _append_line(self.path, event)
        self.next_seq += 1
        return event


def send_command(run_dir: Path | str, cmd: str, **args: Any) -> dict[str, Any]:
    """Append a command to ``control.jsonl`` (used by the UI and the CLI)."""
    if cmd not in COMMANDS:
        raise ValueError(f"unknown command {cmd!r}; expected one of {sorted(COMMANDS)}")
    record = {"id": uuid.uuid4().hex[:12], "ts": _now(), "cmd": cmd, **args}
    _append_line(Path(run_dir) / CONTROL_FILE, record)
    return record


def pending_commands(run_dir: Path | str) -> list[dict[str, Any]]:
    """Commands in control.jsonl that the engine has not acknowledged yet."""
    run_dir = Path(run_dir)
    handled = {e["cmd_id"] for e in read_events(run_dir)
               if e.get("type") in ("control_ack", "control_reject") and "cmd_id" in e}
    return [c for c in _read_complete_lines(run_dir / CONTROL_FILE)
            if c.get("id") and c["id"] not in handled]


def validate_command(command: dict[str, Any]) -> str | None:
    """Return an error message, or None if the command is well formed."""
    cmd = command.get("cmd")
    if cmd not in COMMANDS:
        return f"unknown command {cmd!r}"
    if cmd == "hint":
        text = command.get("text")
        if not isinstance(text, str):
            return "hint needs a text string"
        if len(text) > MAX_HINT_CHARS:
            return f"hint longer than {MAX_HINT_CHARS} characters"
    if cmd == "set":
        field = command.get("field")
        if field not in STEERABLE_FIELDS:
            return f"field {field!r} is not steerable; expected one of {sorted(STEERABLE_FIELDS)}"
        typ, lo, hi = STEERABLE_FIELDS[field]
        value = command.get("value")
        if isinstance(value, bool) or not isinstance(value, typ):
            return f"{field} must be an integer"
        if not lo <= value <= hi:
            return f"{field} must be between {lo} and {hi}"
    return None


class ControlChannel:
    """Engine side of ``control.jsonl``.

    A command counts as handled once its id appears in a ``control_ack`` or
    ``control_reject`` event, so commands are applied exactly once even across
    a resume.
    """

    def __init__(self, run_dir: Path | str, events: EventLog,
                 poll_interval: float = 1.0,
                 sleep: Callable[[float], None] = time.sleep):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / CONTROL_FILE
        self.events = events
        self.poll_interval = poll_interval
        self.sleep = sleep
        self.handled: set[str] = {
            e["cmd_id"] for e in read_events(self.run_dir)
            if e.get("type") in ("control_ack", "control_reject") and "cmd_id" in e
        }

    def pending(self) -> list[dict[str, Any]]:
        """Commands not yet acknowledged, in the order they were sent."""
        return [c for c in _read_complete_lines(self.path)
                if c.get("id") and c["id"] not in self.handled]

    def ack(self, command: dict[str, Any], generation: int, **extra: Any) -> None:
        self.handled.add(command["id"])
        fields = {k: v for k, v in command.items() if k not in ("id", "ts")}
        self.events.emit("control_ack", cmd_id=command["id"], gen=generation, **fields, **extra)

    def reject(self, command: dict[str, Any], generation: int, reason: str) -> None:
        self.handled.add(command["id"])
        self.events.emit("control_reject", cmd_id=command["id"], gen=generation,
                         cmd=command.get("cmd"), reason=reason)


def backfill(run_dir: Path | str, force: bool = False) -> int:
    """Rebuild ``events.jsonl`` for a run recorded before the event log existed.

    Uses the committed ``generation_NNNN.json`` checkpoints, which only hold
    the surviving population of each generation, so candidates culled within
    a generation do not appear. Roles come from ``prompt_logs`` when present.
    Returns the number of events written.
    """
    run_dir = Path(run_dir)
    path = run_dir / EVENTS_FILE
    if path.exists():
        if not force:
            raise FileExistsError(f"{path} exists; use force=True to rebuild it")
        path.unlink()

    gens = []
    for p in sorted(run_dir.glob("generation_*.json")):
        try:
            gens.append(json.loads(p.read_text()))
        except (OSError, json.JSONDecodeError):
            continue
    if not gens:
        return 0

    roles: dict[str, str] = {}
    for p in sorted((run_dir / "prompt_logs").glob("call_*.json")):
        try:
            entry = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if entry.get("type") == "repair" and entry.get("candidate_id"):
            roles[entry["candidate_id"]] = "repair"

    config: dict[str, Any] = {}
    try:
        import yaml  # optional; only used for run metadata
        config = yaml.safe_load((run_dir / "config.yaml").read_text()) or {}
    except Exception:
        pass

    log = EventLog(run_dir)
    first, last = gens[0], gens[-1]
    log.emit("run_start", ts=first.get("timestamp"), run_id=first.get("run_id", run_dir.name),
             problem=first.get("problem"), provider=config.get("provider"),
             model=config.get("model"), population_size=config.get("population_size"),
             max_generations=config.get("max_generations"),
             model_call_budget=config.get("model_call_budget"),
             resumed=False, generation=0, backfilled=True)
    seen: set[str] = set()
    for g in gens:
        gen, ts = g["generation"], g.get("timestamp")
        log.emit("gen_start", ts=ts, gen=gen)
        cands = g.get("candidates", [])
        for c in cands:
            if c["id"] in seen:
                continue
            seen.add(c["id"])
            parents = c.get("parent_ids") or []
            role = roles.get(c["id"]) or ("seed" if gen == 1 else "mutate" if parents else "fresh")
            log.emit("candidate_generated", ts=ts, id=c["id"], gen=gen,
                     parent_ids=parents, role=role)
            log.emit("candidate_verified", ts=ts, id=c["id"], gen=gen,
                     state=c.get("state"), fitness=c.get("fitness"),
                     work_ratio=c.get("work_ratio"), timeout=c.get("timeout", False),
                     tests_passed=c.get("tests_passed"), tests_total=c.get("tests_total"),
                     failing_case=c.get("failing_case"), error=c.get("error_message"))
            if c.get("reflection_path"):
                log.emit("candidate_reflected", ts=ts, id=c["id"], gen=gen,
                         reflection_path=c["reflection_path"])
        ranked = sorted(cands, key=lambda c: (c.get("state") != "PASS", -c.get("fitness", 0.0),
                                              c.get("work_ratio") if c.get("work_ratio") is not None
                                              else float("inf")))
        top = ranked[0] if ranked else None
        log.emit("gen_committed", ts=ts, gen=gen,
                 population=[{"id": c["id"], "parent_ids": c.get("parent_ids") or [],
                              "state": c.get("state"), "fitness": c.get("fitness"),
                              "work_ratio": c.get("work_ratio")} for c in cands],
                 best_id=top["id"] if top else None,
                 best_fitness=max((c.get("fitness", 0.0) for c in cands), default=0.0),
                 best_work_ratio=top.get("work_ratio") if top else None,
                 model_calls=g.get("model_calls"), stop_reason=g.get("stop_reason"))
    top_last = next((e for e in reversed(read_events(run_dir)) if e["type"] == "gen_committed"), {})
    log.emit("run_end", ts=last.get("timestamp"), stop_reason=last.get("stop_reason"),
             generation=last["generation"], best_candidate_id=top_last.get("best_id"),
             best_fitness=top_last.get("best_fitness"),
             best_work_ratio=top_last.get("best_work_ratio"),
             model_calls=last.get("model_calls"))
    return log.next_seq


# -- run summaries (web UI and `evoalgo status --json`) -----------------------

def engine_state(run_dir: Path) -> str:
    """"alive" if the engine that wrote engine.json still runs on this host,
    "gone" if engine.json is left behind by a dead process, "none" otherwise."""
    try:
        info = json.loads((run_dir / ENGINE_FILE).read_text())
    except FileNotFoundError:
        # A coding agent drives harness runs (evoalgo init) and no engine
        # process exists: live while checks keep coming, "gone" after
        # HARNESS_IDLE_SECONDS without one (the agent stopped without finish).
        if (run_dir / "HARNESS").exists():
            try:
                idle = time.time() - (run_dir / EVENTS_FILE).stat().st_mtime
            except FileNotFoundError:
                return "none"
            return "alive" if idle < HARNESS_IDLE_SECONDS else "gone"
        return "none"
    except (OSError, json.JSONDecodeError):
        return "gone"
    if info.get("host") != socket.gethostname():
        return "gone"  # ponytail: a run on another host is reported as gone
    try:
        os.kill(int(info["pid"]), 0)
    except PermissionError:
        return "alive"
    except (OSError, KeyError, TypeError, ValueError):
        return "gone"
    return "alive"


def run_state(events: list[dict[str, Any]], engine: str = "alive") -> str:
    if not events:
        return "empty"
    if events[-1].get("type") == "run_end":
        return "done"
    if engine != "alive":
        return "interrupted"
    paused = False
    for e in events:
        if e.get("type") == "paused":
            paused = True
        elif e.get("type") == "resumed":
            paused = False
    return "paused" if paused else "running"


def summarize(run_dir: Path) -> dict[str, Any]:
    events = read_events(run_dir)
    engine = engine_state(run_dir)
    summary: dict[str, Any] = {"run_id": run_dir.name, "has_events": bool(events),
                               "engine": engine,
                               "state": run_state(events, engine) if events else "no_events"}
    if not events:
        return summary
    start = next((e for e in events if e["type"] == "run_start"), {})
    commits = [e for e in events if e["type"] == "gen_committed"]
    last = commits[-1] if commits else {}
    summary.update(
        problem=start.get("problem"), model=start.get("model"),
        pack=start.get("pack"), research_goal=start.get("research_goal"),
        max_generations=start.get("max_generations"),
        generation=last.get("gen", 0), best_id=last.get("best_id"),
        best_fitness=last.get("best_fitness"), best_work_ratio=last.get("best_work_ratio"),
        model_calls=last.get("model_calls"), started=start.get("ts"),
        updated=events[-1].get("ts"), events=len(events),
        history=[c.get("best_work_ratio") for c in commits],
    )
    return summary
