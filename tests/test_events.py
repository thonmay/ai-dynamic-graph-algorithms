# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tests for the event log, control channel, steering and backfill."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from evoalgo.cli import _generate_known_good_candidate
from evoalgo.config import Bound, RunConfig
from evoalgo.events import (
    CONTROL_FILE,
    ENGINE_FILE,
    EVENTS_FILE,
    ControlChannel,
    EventLog,
    backfill,
    read_events,
    send_command,
    validate_command,
)
from evoalgo.orchestrator import Orchestrator

REPO = Path(__file__).resolve().parents[1]


# -- event log ---------------------------------------------------------------

def test_seq_continues_after_reopen(tmp_path):
    log = EventLog(tmp_path)
    log.emit("a")
    log.emit("b", x=1)
    assert EventLog(tmp_path).emit("c")["seq"] == 2
    assert [e["type"] for e in read_events(tmp_path)] == ["a", "b", "c"]
    assert [e["seq"] for e in read_events(tmp_path, since=1)] == [1, 2]


def test_partial_and_malformed_lines_are_skipped(tmp_path):
    EventLog(tmp_path).emit("ok")
    with open(tmp_path / EVENTS_FILE, "a") as f:
        f.write("not json\n")
        f.write('{"seq": 9, "type": "half"')  # no newline: still being written
    events = read_events(tmp_path)
    assert [e["type"] for e in events] == ["ok"]


# -- command validation ------------------------------------------------------

@pytest.mark.parametrize("cmd,ok", [
    ({"cmd": "pause"}, True),
    ({"cmd": "hint", "text": "try lazy repair"}, True),
    ({"cmd": "hint", "text": "x" * 2001}, False),
    ({"cmd": "hint"}, False),
    ({"cmd": "set", "field": "population_size", "value": 4}, True),
    ({"cmd": "set", "field": "population_size", "value": 0}, False),
    ({"cmd": "set", "field": "population_size", "value": True}, False),
    ({"cmd": "set", "field": "timeout_seconds", "value": 5}, False),
    ({"cmd": "rm -rf"}, False),
])
def test_validate_command(cmd, ok):
    assert (validate_command(cmd) is None) == ok


def test_send_command_rejects_unknown(tmp_path):
    with pytest.raises(ValueError):
        send_command(tmp_path, "explode")


def test_commands_are_handled_once_across_restarts(tmp_path):
    log = EventLog(tmp_path)
    send_command(tmp_path, "pause")
    channel = ControlChannel(tmp_path, log)
    [command] = channel.pending()
    channel.ack(command, generation=3)
    assert channel.pending() == []
    # A new channel (e.g. after resume) rebuilds "handled" from the event log.
    assert ControlChannel(tmp_path, EventLog(tmp_path)).pending() == []
    ack = read_events(tmp_path)[-1]
    assert ack["type"] == "control_ack" and ack["cmd"] == "pause" and ack["gen"] == 3


# -- orchestrator integration ------------------------------------------------

class FakeProvider:
    """Writes a known-good candidate instead of calling an agent."""

    def __init__(self, problem: str):
        self.code = _generate_known_good_candidate(problem)
        self.call_count = 0
        self.hint: str | None = None
        self.hints_seen: list[str | None] = []

    def generate(self, problem_name, parent_code, candidate_filename, generation, workdir):
        self.call_count += 1
        self.hints_seen.append(self.hint)
        path = Path(workdir) / "candidates" / candidate_filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.code)
        return "ok"

    repair = None
    reflect = None


def make_orchestrator(tmp_path, max_generations=3) -> Orchestrator:
    config = RunConfig(
        problem="dynamic_bfs", population_size=2, max_generations=max_generations,
        elitism_k=1, early_stop_on_success=False, timeout_seconds=30,
        bound=Bound(n_max=2, n_random=0, seq_len_max=2, seq_count=1, seed=7),
        workdir=str(tmp_path),
    )
    orch = Orchestrator(config=config, run_id="t")
    orch.provider = FakeProvider(config.problem)
    orch.reflector.provider = orch.provider
    orch.control.sleep = lambda _s: None
    return orch


def types(run_dir):
    return [e["type"] for e in read_events(run_dir)]


def test_run_emits_full_event_stream(tmp_path):
    orch = make_orchestrator(tmp_path)
    summary = orch.run()
    t = types(orch.run_dir)
    assert t[0] == "run_start" and t[-1] == "run_end"
    assert t.count("gen_committed") == 3 == summary["generation"]
    verified = [e for e in read_events(orch.run_dir) if e["type"] == "candidate_verified"]
    assert verified and all(e["state"] == "PASS" and e["fitness"] == 1.0 for e in verified)
    seqs = [e["seq"] for e in read_events(orch.run_dir)]
    assert seqs == list(range(len(seqs)))


def test_stop_before_start_ends_without_model_calls(tmp_path):
    orch = make_orchestrator(tmp_path)
    send_command(orch.run_dir, "stop")
    summary = orch.run()
    assert summary["stop_reason"] == "user_stop"
    assert orch.provider.call_count == 0
    assert "control_ack" in types(orch.run_dir)


def test_pause_blocks_until_resume(tmp_path):
    orch = make_orchestrator(tmp_path, max_generations=2)
    send_command(orch.run_dir, "pause")
    polls = []

    def sleep(_s):
        polls.append(1)
        if len(polls) == 2:
            send_command(orch.run_dir, "resume")

    orch.control.sleep = sleep
    summary = orch.run()
    assert len(polls) == 2
    assert summary["stop_reason"] == "max_generations"
    acks = [e["cmd"] for e in read_events(orch.run_dir) if e["type"] == "control_ack"]
    assert acks == ["pause", "resume"]


def test_steering_hint_and_population(tmp_path):
    orch = make_orchestrator(tmp_path, max_generations=2)
    send_command(orch.run_dir, "hint", text="prefer incremental BFS")
    send_command(orch.run_dir, "set", field="population_size", value=3)
    send_command(orch.run_dir, "set", field="population_size", value=0)  # invalid
    orch.run()
    assert orch.provider.hints_seen and all(h == "prefer incremental BFS"
                                            for h in orch.provider.hints_seen)
    assert orch.config.population_size == 3 and orch.population.max_size == 3
    saved = RunConfig.load(orch.run_dir / "config.yaml")
    assert saved.population_size == 3
    rejects = [e for e in read_events(orch.run_dir) if e["type"] == "control_reject"]
    assert len(rejects) == 1 and "between" in rejects[0]["reason"]


def test_population_below_elitism_is_rejected(tmp_path):
    orch = make_orchestrator(tmp_path, max_generations=1)
    orch.config.elitism_k = 2
    send_command(orch.run_dir, "set", field="population_size", value=1)
    orch.run()
    [reject] = [e for e in read_events(orch.run_dir) if e["type"] == "control_reject"]
    assert "elitism_k" in reject["reason"]
    assert orch.config.population_size == 2


class HookProvider(FakeProvider):
    """FakeProvider that runs a callback inside the n-th generate call."""

    def __init__(self, problem, run_dir, on_call):
        super().__init__(problem)
        self.run_dir = run_dir
        self.on_call = on_call

    def generate(self, *args, **kwargs):
        out = super().generate(*args, **kwargs)
        self.on_call(self.call_count, self.run_dir)
        return out


def hooked(tmp_path, on_call, max_generations=1):
    orch = make_orchestrator(tmp_path, max_generations=max_generations)
    orch.provider = HookProvider(orch.config.problem, orch.run_dir, on_call)
    orch.reflector.provider = orch.provider
    return orch


def test_pause_applies_before_next_agent_call(tmp_path):
    def on_call(n, run_dir):
        if n == 1:
            send_command(run_dir, "pause")

    orch = hooked(tmp_path, on_call)
    orch.control.sleep = lambda _s: send_command(orch.run_dir, "resume")
    orch.run()
    seq = [(e["type"], e.get("id") or e.get("cmd")) for e in read_events(orch.run_dir)
           if e["type"] in ("agent_call_start", "agent_call_end", "control_ack", "paused", "resumed")]
    assert seq == [
        ("agent_call_start", "gen001_c01"), ("agent_call_end", "gen001_c01"),
        ("control_ack", "pause"), ("paused", None), ("control_ack", "resume"), ("resumed", None),
        ("agent_call_start", "gen001_c02"), ("agent_call_end", "gen001_c02"),
    ]
    paused = next(e for e in read_events(orch.run_dir) if e["type"] == "paused")
    assert paused["before"] == {"role": "seed", "id": "gen001_c02"} and paused["gen"] == 1


def test_stop_mid_generation_commits_what_was_produced(tmp_path):
    def on_call(n, run_dir):
        if n == 1:
            send_command(run_dir, "stop")

    orch = hooked(tmp_path, on_call, max_generations=3)
    summary = orch.run()
    assert summary["stop_reason"] == "user_stop"
    assert orch.provider.call_count == 1
    events = read_events(orch.run_dir)
    verified = [e["id"] for e in events if e["type"] == "candidate_verified"]
    committed = [e["gen"] for e in events if e["type"] == "gen_committed"]
    assert verified == ["gen001_c01"] and committed == [1]
    assert events[-1]["type"] == "run_end" and events[-1]["stop_reason"] == "user_stop"


def test_agent_calls_paired_and_engine_file_lifecycle(tmp_path):
    seen = []
    orch = hooked(tmp_path, lambda n, run_dir: seen.append((run_dir / ENGINE_FILE).exists()))
    orch.run()
    events = read_events(orch.run_dir)
    starts = [(e["role"], e["id"]) for e in events if e["type"] == "agent_call_start"]
    ends = [(e["role"], e["id"]) for e in events if e["type"] == "agent_call_end"]
    assert starts == ends and len(starts) == orch.provider.call_count
    assert all(e["ok"] and e["duration_s"] >= 0 for e in events if e["type"] == "agent_call_end")
    assert seen and all(seen)
    assert not (orch.run_dir / ENGINE_FILE).exists()


# -- backfill ----------------------------------------------------------------

def test_backfill_existing_run(tmp_path):
    src = REPO / "runs" / "mcs_pressure_e2e"
    if not src.exists():
        pytest.skip("reference run not present")
    run = tmp_path / "mcs_pressure_e2e"
    run.mkdir()
    for name in ["config.yaml", *[p.name for p in src.glob("generation_*.json")]]:
        shutil.copy(src / name, run / name)
    shutil.copytree(src / "prompt_logs", run / "prompt_logs")

    n = backfill(run)
    events = read_events(run)
    assert n == len(events) > 0
    committed = [e for e in events if e["type"] == "gen_committed"]
    assert [e["gen"] for e in committed] == [1, 2, 3, 4, 5]
    end = events[-1]
    assert end["type"] == "run_end" and end["best_candidate_id"] == "gen003_c01"
    assert end["stop_reason"] == "max_generations"
    generated = {e["id"]: e for e in events if e["type"] == "candidate_generated"}
    assert len(generated) == 7
    assert generated["gen003_c01"]["parent_ids"] == ["gen002_c01"]
    assert generated["gen001_c01"]["role"] == "seed"

    with pytest.raises(FileExistsError):
        backfill(run)
    assert backfill(run, force=True) == n
    assert not (run / CONTROL_FILE).exists()
