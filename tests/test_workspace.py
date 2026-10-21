"""Harness workspaces: init, check, finish, skill install, run summaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evoalgo import workspace as wsm
from evoalgo.cli import _generate_known_bad_candidate, _generate_known_good_candidate, main
from evoalgo.events import engine_state, read_events, summarize

GOOD = _generate_known_good_candidate("dynamic_bfs")
BAD = _generate_known_bad_candidate("dynamic_bfs")


@pytest.fixture()
def ws(tmp_path):
    return wsm.init_workspace("dynamic_bfs", tmp_path / "work", runs_root=tmp_path / "runs",
                              run_id="h1", goal="  be fast  ", harness="codex")


def test_init_creates_agent_files_and_run(ws, tmp_path):
    for name in ("program.md", "candidate.py", "results.tsv", "workspace.json"):
        assert (ws.dir / name).is_file(), name
    program = (ws.dir / "program.md").read_text()
    assert "State contract" in program and "'parent'" in program
    assert "'distances'" in program and "be fast" in program and "evoalgo check" in program
    assert (ws.run_dir / "config.yaml").is_file() and (ws.run_dir / "HARNESS").is_file()
    start = read_events(ws.run_dir)[0]
    assert start["type"] == "run_start" and start["provider"] == "harness" and start["model"] == "codex"
    # No engine process, but the run is live until finish.
    assert engine_state(ws.run_dir) == "alive"
    with pytest.raises(FileExistsError):
        wsm.init_workspace("dynamic_bfs", ws.dir, runs_root=tmp_path / "runs", run_id="h2")
    with pytest.raises(FileExistsError):
        wsm.init_workspace("dynamic_bfs", tmp_path / "other", runs_root=tmp_path / "runs", run_id="h1")


def test_check_records_like_a_run(ws):
    (ws.dir / "candidate.py").write_text(BAD)
    bad = wsm.check(ws, level="examples", note="stale\tstate\nline")
    assert bad["verdict"] == "FAIL" and "first_failure" in bad and bad["check"] == 1
    (ws.dir / "candidate.py").write_text(GOOD)
    good = wsm.check(ws, level="examples")
    assert good["verdict"] == "PASS" and good["candidate_id"] == "gen002_c01"
    # Snapshots are kept even after the agent overwrites candidate.py.
    assert (ws.run_dir / "candidates" / "gen001_c01.py").read_text() == BAD
    rows = (ws.dir / "results.tsv").read_text().splitlines()
    assert rows[0].startswith("check\t") and len(rows) == 3
    assert rows[1].split("\t")[-1] == "stale state line"  # note cannot break the TSV
    types = [e["type"] for e in read_events(ws.run_dir)]
    assert types.count("gen_committed") == 2 and types.count("candidate_verified") == 2
    third = wsm.check(ws, level="examples")
    gen3 = next(e for e in read_events(ws.run_dir)
                if e["type"] == "candidate_generated" and e["id"] == third["candidate_id"])
    assert gen3["parent_ids"] == ["gen002_c01"]  # lineage: last passing check


def test_final_and_finish(ws):
    (ws.dir / "candidate.py").write_text(GOOD)
    # Keep the "full" grade small for the test: shrink the run's bound.
    from evoalgo.config import RunConfig
    cfg = RunConfig.load(ws.run_dir / "config.yaml")
    cfg.bound.n_max, cfg.bound.n_random, cfg.bound.seq_count = 3, 0, 1
    cfg.save(ws.run_dir / "config.yaml")
    wsm.check(ws, level="examples")
    final = wsm.check(ws, level="full", final=True)
    assert final["verdict"] == "PASS"
    end = wsm.finish(ws)
    assert end["type"] == "run_end" and end["final_grade"]["state"] == "PASS"
    assert end["best_candidate_id"] == final["candidate_id"]  # full level outranks examples
    assert summarize(ws.run_dir)["state"] == "done"


def test_check_finds_workspace_from_subdir_and_rejects_bad_level(ws):
    sub = ws.dir / "notes"
    sub.mkdir()
    assert wsm.Workspace.find(sub).run_dir == ws.run_dir
    with pytest.raises(ValueError):
        wsm.check(ws, level="huge")
    with pytest.raises(FileNotFoundError):
        wsm.Workspace.find(ws.dir.parent.parent / "nowhere")


def test_cli_check_json_and_exit_codes(ws, capsys, monkeypatch):
    monkeypatch.chdir(ws.dir)
    (ws.dir / "candidate.py").write_text(BAD)
    assert main(["check", "--level", "examples"]) == 3
    assert json.loads(capsys.readouterr().out)["verdict"] == "FAIL"
    (ws.dir / "candidate.py").write_text(GOOD)
    assert main(["check", "--level", "examples"]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "PASS"
    assert main(["status", str(ws.run_dir), "--json"]) == 0
    s = json.loads(capsys.readouterr().out)
    assert s["harness"] is True and s["best_candidate_path"].endswith(".py")
    assert main(["history", "--workdir", str(ws.run_dir.parent), "--json"]) == 0
    assert [r["run_id"] for r in json.loads(capsys.readouterr().out)] == ["h1"]
    assert main(["resume", str(ws.run_dir)]) == 1  # harness runs are not engine runs


def test_cli_packs(capsys):
    assert main(["packs"]) == 0
    packs = json.loads(capsys.readouterr().out)
    bfs = next(p for p in packs if p["name"] == "dynamic_bfs")
    assert bfs["tier"] == "calibration" and bfs["question"].endswith("?")


def test_skill_is_valid_agent_skill():
    src = wsm.skill_source()
    text = (src / "SKILL.md").read_text()
    assert text.startswith("---\n")
    front = text.split("---\n")[1]
    import yaml
    meta = yaml.safe_load(front)
    # agentskills.io: name matches the folder, lowercase-hyphen, description <= 1024.
    assert meta["name"] == src.name == "evoalgo"
    assert 0 < len(meta["description"]) <= 1024
    for ref in ("references/orchestrator.md", "references/inspect.md"):
        assert ref in text and (src / ref).is_file()
    # The repo-level discovery links point at the same files.
    repo = Path(__file__).resolve().parents[1]
    for link in (".agents/skills/evoalgo", ".claude/skills/evoalgo", "plugins/evoalgo/skills/evoalgo"):
        assert (repo / link / "SKILL.md").read_text() == text, link


def test_install_skill(tmp_path):
    dests = wsm.install_skill("project", tmp_path)
    assert {d.parent.parent.name for d in dests} == {".agents", ".claude"}
    assert all((d / "SKILL.md").is_file() and (d / "references" / "inspect.md").is_file() for d in dests)
    with pytest.raises(FileExistsError):
        wsm.install_skill("project", tmp_path)
    assert wsm.install_skill("project", tmp_path, force=True) == dests


def test_interrupted_check_closes_its_generation(ws, monkeypatch):
    from evoalgo import verifier as vmod
    (ws.dir / "candidate.py").write_text(GOOD)

    def boom(self, cand):
        raise KeyboardInterrupt
    monkeypatch.setattr(vmod.Verifier, "verify", boom)
    with pytest.raises(KeyboardInterrupt):
        wsm.check(ws, level="examples")
    monkeypatch.undo()
    nxt = wsm.check(ws, level="examples")
    assert nxt["candidate_id"] == "gen002_c01"  # no reuse of the aborted id
    ev = read_events(ws.run_dir)
    assert [e["gen"] for e in ev if e["type"] == "gen_start"] == [1, 2]
    assert [e["gen"] for e in ev if e["type"] == "gen_committed"] == [1, 2]
    aborted = next(e for e in ev if e["type"] == "candidate_verified" and e["id"] == "gen001_c01")
    assert aborted["state"] == "CRASH" and "interrupted" in aborted["error"]


def test_best_is_best_pass_so_far(ws, capsys):
    (ws.dir / "candidate.py").write_text(GOOD)
    good = wsm.check(ws, level="examples")
    (ws.dir / "candidate.py").write_text(BAD)
    wsm.check(ws, level="examples")
    last = [e for e in read_events(ws.run_dir) if e["type"] == "gen_committed"][-1]
    assert last["best_id"] == good["candidate_id"]
    assert main(["status", str(ws.run_dir), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["best_candidate_path"].endswith(f"{good['candidate_id']}.py")


def test_finished_workspace_refuses_more(ws):
    (ws.dir / "candidate.py").write_text(GOOD)
    wsm.check(ws, level="examples")
    wsm.finish(ws)
    with pytest.raises(RuntimeError):
        wsm.check(ws, level="examples")
    with pytest.raises(RuntimeError):
        wsm.finish(ws)


def test_failed_init_leaves_nothing(tmp_path, monkeypatch):
    def broken(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(wsm.EventLog, "emit", broken)
    with pytest.raises(OSError):
        wsm.init_workspace("dynamic_bfs", tmp_path / "w", runs_root=tmp_path / "runs", run_id="r")
    assert not (tmp_path / "runs" / "r").exists()
    assert not any((tmp_path / "w").iterdir())
    monkeypatch.undo()
    assert wsm.init_workspace("dynamic_bfs", tmp_path / "w", runs_root=tmp_path / "runs", run_id="r")


def test_idle_harness_run_counts_as_gone(ws):
    import os
    from evoalgo.events import HARNESS_IDLE_SECONDS
    assert engine_state(ws.run_dir) == "alive"
    old = os.path.getmtime(ws.run_dir / "events.jsonl") - HARNESS_IDLE_SECONDS - 10
    os.utime(ws.run_dir / "events.jsonl", (old, old))
    assert engine_state(ws.run_dir) == "gone"


def test_cli_errors_are_json(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["check"]) == 2
    assert "error" in json.loads(capsys.readouterr().out)


def test_sandbox_leaves_no_temp_files(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)
    from evoalgo.agents.examples import run_examples
    for _ in range(3):
        assert run_examples("dynamic_bfs", GOOD)["verdict"] == "PASS"
    assert list(tmp_path.iterdir()) == []  # the runner is passed with -c, no file
