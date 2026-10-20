"""Tests for the agent layer: tools, api tool loop, mock backend, wiring."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from evoalgo.agents.api import ApiBackend
from evoalgo.agents.base import Task, make_backend
from evoalgo.agents.examples import PUBLIC_N_MAX, run_examples
from evoalgo.agents.harness import EnlcodeBackend
from evoalgo.agents.tools import Toolbox, schemas
from evoalgo.cli import _generate_known_bad_candidate, _generate_known_good_candidate
from evoalgo.config import Bound, RunConfig
from evoalgo.events import read_events
from evoalgo.orchestrator import Orchestrator

GOOD = _generate_known_good_candidate("dynamic_bfs")
BAD = _generate_known_bad_candidate("dynamic_bfs")


def task(tmp_path, role="generate", **kw) -> Task:
    (tmp_path / "candidates").mkdir(exist_ok=True)
    return Task(role=role, candidate_id="gen001_c01", problem="dynamic_bfs",
                problem_prompt="PROBLEM: dynamic_bfs", run_dir=tmp_path, **kw)


# -- tools -------------------------------------------------------------------

def test_tool_paths_are_confined(tmp_path):
    (tmp_path / "candidates" ).mkdir()
    (tmp_path / "candidates" / "gen000_c01.py").write_text("x = 1\n")
    (tmp_path / "config.yaml").write_text("secret: 1\n")
    tb = Toolbox(task(tmp_path), pack_dir=None)
    assert tb.call("read_file", json.dumps({"path": "candidates/gen000_c01.py"})) == "x = 1\n"
    for bad in ("config.yaml", "../etc/passwd", "candidates/../config.yaml", "/etc/passwd",
                "pack/brief.md", "reflections/../../x"):
        assert tb.call("read_file", json.dumps({"path": bad})).startswith("error")
    assert tb.call("rm_rf", "{}").startswith("error: unknown tool")
    assert tb.call("write_candidate", "not json").startswith("error: invalid JSON")
    # A reflect call cannot write candidates.
    rt = Toolbox(task(tmp_path, role="reflect"), pack_dir=None)
    assert rt.call("write_candidate", json.dumps({"code": "x"})).startswith("error: unknown tool")


def test_missing_pack_file_lists_existing(tmp_path):
    pack = tmp_path / "pk"
    pack.mkdir()
    (pack / "brief.md").write_text("b")
    (pack / "problem.yaml").write_text("p")
    (tmp_path / "secret.txt").write_text("s")
    tb = Toolbox(task(tmp_path), pack_dir=pack)
    out = tb.call("read_file", json.dumps({"path": "pack/spec.md"}))
    assert out.startswith("error: no such file") and "brief.md, problem.yaml" in out
    assert "secret" not in tb.call("read_file", json.dumps({"path": "pack/../secret.txt"}))
    # reflections/ not created yet: must not fall back to listing the run dir
    run = Toolbox(task(tmp_path), pack_dir=None).call("read_file", json.dumps({"path": "reflections"}))
    assert "secret" not in run and "candidates" not in run.split("files in")[-1]


def test_problem_prompt_has_state_contract(tmp_path):
    from evoalgo.llm_provider import LLMProvider
    cfg = RunConfig(problem="dynamic_dfs", provider="mock")
    text = LLMProvider(cfg, tmp_path)._build_problem_prompt("dynamic_dfs")
    assert "STATE CONTRACT" in text and "'finish'" in text


def test_write_edit_and_examples(tmp_path):
    t = task(tmp_path)
    tb = Toolbox(t, pack_dir=None)
    assert tb.call("edit_candidate", json.dumps({"old": "a", "new": "b"})).startswith("error")
    assert tb.call("write_candidate", json.dumps({"code": BAD})).startswith("wrote candidates/gen001_c01.py")
    report = json.loads(tb.call("run_examples", "{}"))
    assert report["verdict"] == "FAIL" and "first_failure" in report
    assert tb.call("edit_candidate", json.dumps({"old": "state", "new": "s"})).startswith("error: 'old' must occur exactly once")
    tb.call("write_candidate", json.dumps({"code": GOOD}))
    report = json.loads(tb.call("run_examples", "{}"))
    assert report["verdict"] == "PASS" and f"n <= {PUBLIC_N_MAX}" in report["scope"]
    assert tb.examples_runs == 2


def test_public_examples_known_good_for_every_problem():
    for p in ("dynamic_bfs", "dynamic_dfs", "dynamic_mcs", "dynamic_lbfs", "dynamic_scc", "reachability"):
        assert run_examples(p, _generate_known_good_candidate(p))["verdict"] == "PASS", p
        assert run_examples(p, _generate_known_bad_candidate(p))["verdict"] in ("FAIL", "CRASH"), p


def test_schemas_per_role():
    names = lambda r: [s["function"]["name"] for s in schemas(r)]  # noqa: E731
    assert names("generate") == names("repair") == ["read_file", "write_candidate", "edit_candidate", "run_examples"]
    assert names("reflect") == ["read_file", "write_reflection"]


# -- api tool loop with a scripted client ------------------------------------

class ScriptedClient:
    """Mimics openai.OpenAI().chat.completions.create with canned turns."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.requests = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        self.requests.append({**kw, "messages": [dict(m) for m in kw["messages"]]})
        content, calls = self.turns.pop(0)
        tcs = [NS(id=f"t{i}", function=NS(name=n, arguments=json.dumps(a))) for i, (n, a) in enumerate(calls)]
        msg = NS(content=content, tool_calls=tcs or None)
        return NS(choices=[NS(message=msg, finish_reason="tool_calls" if tcs else "stop")],
                  usage=NS(prompt_tokens=100, completion_tokens=20))


def api_config(**kw):
    return RunConfig(problem="dynamic_bfs", provider="api", api_base_url="ericai", model="m", **kw)


def test_api_loop_writes_checks_and_fixes(tmp_path):
    client = ScriptedClient([
        (None, [("write_candidate", {"code": BAD})]),
        (None, [("run_examples", {})]),
        (None, [("write_candidate", {"code": GOOD}), ("run_examples", {})]),
        ("CANDIDATE: candidates/gen001_c01.py\nEXAMPLES: PASS", []),
    ])
    backend = ApiBackend(api_config(), tmp_path, client=client)
    result = backend.run(task(tmp_path))
    assert result.ok and result.steps == 4 and result.summary.startswith("CANDIDATE")
    assert result.tool_calls == ["write_candidate", "run_examples", "write_candidate", "run_examples"]
    assert result.usage == {"prompt_tokens": 400, "completion_tokens": 80}
    # The model saw the FAIL report from its first examples run.
    tool_msgs = [m for m in client.requests[2]["messages"] if m["role"] == "tool"]
    assert '"verdict": "FAIL"' in tool_msgs[-1]["content"]
    assert client.requests[0]["tools"] and client.requests[0]["model"] == "m"
    log = json.loads((tmp_path / "prompt_logs" / "call_0001.json").read_text())
    assert log["ok"] and log["examples_runs"] == 2 and log["backend"] == "api"


def test_api_loop_step_limit_and_errors(tmp_path):
    client = ScriptedClient([(None, [("read_file", {"path": "x"})])] * 3)
    r = ApiBackend(api_config(agent_max_steps=3), tmp_path, client=client).run(task(tmp_path))
    assert not r.ok and "step limit" in r.error

    class Boom:
        chat = NS(completions=NS(create=lambda **kw: (_ for _ in ()).throw(RuntimeError("503"))))
    r = ApiBackend(api_config(), tmp_path, client=Boom()).run(task(tmp_path))
    assert not r.ok and "503" in r.error


def test_api_thinking_off_and_length_nudge(tmp_path):
    class LengthThenWrite(ScriptedClient):
        def _create(self, **kw):
            if not self.requests:  # a reasoning model burning the whole budget
                self.requests.append({**kw, "messages": [dict(m) for m in kw["messages"]]})
                msg = NS(content="", tool_calls=None)
                return NS(choices=[NS(message=msg, finish_reason="length")], usage=None)
            return super()._create(**kw)

    client = LengthThenWrite([(None, [("write_candidate", {"code": GOOD})]), ("done", [])])
    r = ApiBackend(api_config(), tmp_path, client=client).run(task(tmp_path))
    assert r.ok and r.steps == 3
    assert client.requests[0]["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert "hit the output limit" in client.requests[1]["messages"][-1]["content"]
    on = ApiBackend(api_config(agent_thinking=True), tmp_path, client=client)
    assert on._extra() == {}


def test_api_missing_key_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    cfg = RunConfig(problem="dynamic_bfs", provider="api", api_base_url="openrouter", model="m")
    r = ApiBackend(cfg, tmp_path).run(task(tmp_path))
    assert not r.ok and "OPENROUTER_API_KEY" in r.error


# -- config, harness command, mock run ---------------------------------------

def test_config_validation_for_api():
    errs = RunConfig(problem="dynamic_bfs", provider="api").validate()
    assert any("api_base_url" in e for e in errs) and any("model id" in e for e in errs)
    assert not RunConfig(problem="dynamic_bfs", provider="mock").validate()
    assert any("provider" in e for e in RunConfig(problem="dynamic_bfs", provider="x").validate())
    d = api_config(agent_max_steps=7).to_dict()
    assert d["api_base_url"] == "ericai" and d["agent_max_steps"] == 7 and "bound" in d


def test_enlcode_command_and_parse(tmp_path):
    cfg = RunConfig(problem="dynamic_bfs", provider="enlcode", model="ericai/x", harness_bin="/bin/enl")
    b = EnlcodeBackend(cfg, tmp_path)
    cmd = b.command(task(tmp_path, role="repair"), "PROMPT")
    assert cmd[:2] == ["/bin/enl", "run"] and ["--agent", "algorithm-repairer"] == cmd[cmd.index("--agent"):cmd.index("--agent") + 2]
    assert cmd[-1] == "PROMPT" and "-m" in cmd
    out = "\n".join(json.dumps(e) for e in [
        {"type": "text", "part": {"text": "first"}},
        {"type": "step_finish", "part": {"tokens": {"input": 10, "output": 3}}},
        {"type": "text", "part": {"text": "final"}}])
    assert b.parse(out) == ("final", {"prompt_tokens": 10, "completion_tokens": 3})
    assert make_backend(RunConfig(provider="mock"), tmp_path).name == "mock"


def test_mock_run_end_to_end(tmp_path):
    cfg = RunConfig(problem="dynamic_bfs", provider="mock", population_size=2, max_generations=2,
                    elitism_k=1, early_stop_on_success=False, mock_script=["bad", "good"],
                    bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                    search_n_max=2, search_seq_count=1, workdir=str(tmp_path))
    summary = Orchestrator(cfg, run_id="m").run()
    run_dir = tmp_path / "m"
    events = read_events(run_dir)
    verified = {e["id"]: e["state"] for e in events if e["type"] == "candidate_verified"}
    assert verified["gen001_c01"] == "FAIL" and verified["gen001_c02"] == "PASS"
    assert "gen001_c01" in {e["id"] for e in events if e["type"] == "candidate_reflected"}
    assert summary["best_fitness"] == 1.0
    assert (run_dir / "reflections" / "gen001_c01.md").is_file()
    assert len(list((run_dir / "prompt_logs").glob("call_*.json"))) == summary["model_calls"]
    # Search grade on n <= 2 during the run, final grade on the full bound (n <= 3) at the end.
    assert summary["search_grade"]["n_max"] == 2
    final = summary["final_grade"]
    assert final["state"] == "PASS" and final["n_max"] == 3 and final["tests_total"] > 0
    graded = [e for e in events if e["type"] == "final_graded"]
    assert len(graded) == 1 and graded[0]["id"] == summary["best_candidate_id"]
    assert events[-1]["type"] == "run_end" and events[-1]["final_grade"]["state"] == "PASS"
    search_total = next(e["tests_total"] for e in events
                        if e["type"] == "candidate_verified" and e["id"] == final["id"])
    assert final["tests_total"] > search_total


# A plain BFS that skips vertex 2 entirely: right for n <= 2, wrong for n = 3.
_SMALL_ONLY_BFS = '''
from collections import deque

def init(graph):
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        for v in range(min(n, 2)):
            if graph[u][v] and dist[v] < 0:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return {"parent": parent, "distances": dist}

def insert_edge(graph, edge, state):
    return init(graph)

def delete_edge(graph, edge, state):
    return init(graph)
'''


def test_final_grade_tries_next_passing(tmp_path, monkeypatch):
    """A search PASS that fails the full bound does not end the final grade."""
    cfg = RunConfig(problem="dynamic_bfs", provider="mock", population_size=2, max_generations=1,
                    elitism_k=1, early_stop_on_success=False,
                    mock_script=["code:" + _SMALL_ONLY_BFS, "good"],
                    bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                    search_n_max=2, search_seq_count=1, workdir=str(tmp_path))
    from evoalgo import orchestrator as orch_mod
    # Rank the small-only candidate first regardless of measured work.
    monkeypatch.setattr(orch_mod, "_rank_key", lambda c: (c.id != "gen001_c01",))
    summary = Orchestrator(cfg, run_id="fb").run()
    events = read_events(tmp_path / "fb")
    verified = {e["id"]: e["state"] for e in events if e["type"] == "candidate_verified"}
    assert verified == {"gen001_c01": "PASS", "gen001_c02": "PASS"}
    graded = [(e["id"], e["state"]) for e in events if e["type"] == "final_graded"]
    assert graded == [("gen001_c01", "FAIL"), ("gen001_c02", "PASS")]
    assert summary["final_grade"]["id"] == "gen001_c02"
    assert summary["final_grade"]["state"] == "PASS"


def _jwt(seconds_left: float) -> str:
    import base64
    import time as _t
    body = base64.urlsafe_b64encode(json.dumps({"exp": _t.time() + seconds_left}).encode()).decode().rstrip("=")
    return f"h.{body}.s"


def test_ericai_refresh_writes_fresh_token(tmp_path, monkeypatch):
    from evoalgo.agents import api
    token_file = tmp_path / ".ericai_token_env"
    token_file.write_text(f"export ERICAI_ACCESS_TOKEN={_jwt(60)}\n")
    fresh = _jwt(5400)
    cli = tmp_path / "ericai"
    cli.write_text(f"#!/bin/sh\necho {fresh}\n")
    cli.chmod(0o755)
    monkeypatch.setattr(api, "ERICAI_TOKEN_FILE", token_file)
    monkeypatch.setattr(api, "ERICAI_CLI", cli)
    assert api.refresh_ericai_token() is True
    assert api._read_key("ERICAI_ACCESS_TOKEN") == fresh
    assert oct(token_file.stat().st_mode & 0o777) == "0o600"
    # A fresh token is not refreshed again unless forced.
    cli.write_text("#!/bin/sh\nexit 1\n")
    assert api.refresh_ericai_token() is True
    assert api.refresh_ericai_token(force=True) is False
    assert api._read_key("ERICAI_ACCESS_TOKEN") == fresh  # failed refresh keeps the old file


def test_ericai_refresh_rejects_bad_output(tmp_path, monkeypatch):
    from evoalgo.agents import api
    token_file = tmp_path / ".ericai_token_env"
    token_file.write_text(f"export ERICAI_ACCESS_TOKEN={_jwt(60)}\n")
    cli = tmp_path / "ericai"
    cli.write_text("#!/bin/sh\necho please log in in a browser\n")
    cli.chmod(0o755)
    monkeypatch.setattr(api, "ERICAI_TOKEN_FILE", token_file)
    monkeypatch.setattr(api, "ERICAI_CLI", cli)
    assert api.refresh_ericai_token() is False
    assert api._jwt_seconds_left(api._read_key("ERICAI_ACCESS_TOKEN")) < 120


def test_no_reflection_ablation(tmp_path):
    cfg = RunConfig(problem="dynamic_bfs", provider="mock", population_size=2, max_generations=2,
                    elitism_k=1, early_stop_on_success=False, mock_script=["bad", "bad", "good", "good"],
                    reflection=False,
                    bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                    search_n_max=2, search_seq_count=1, workdir=str(tmp_path))
    summary = Orchestrator(cfg, run_id="noref").run()
    events = read_events(tmp_path / "noref")
    assert not [e for e in events if e["type"] == "candidate_reflected"]
    assert not [e for e in events if e["type"] == "candidate_generated" and e.get("role") == "repair"]
    roles = {e["role"] for e in events if e["type"] == "agent_call_start"}
    assert roles == {"seed", "mutate"}  # no reflect, no repair calls
    assert summary["model_calls"] == len([e for e in events if e["type"] == "agent_call_start"])


def test_resume_keeps_call_count(tmp_path):
    """A resumed run continues counting calls, so the budget covers the whole run."""
    base = dict(problem="dynamic_bfs", provider="mock", population_size=2, elitism_k=1,
                early_stop_on_success=False, mock_script=["bad"] * 20, model_call_budget=100,
                bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                search_n_max=2, search_seq_count=1, workdir=str(tmp_path), selection_seed=7)
    first = Orchestrator(RunConfig(max_generations=1, **base), run_id="r").run()
    second = Orchestrator(RunConfig(max_generations=2, **base), run_id="r").run()
    calls = [e for e in read_events(tmp_path / "r") if e["type"] == "agent_call_end"]
    assert first["model_calls"] > 0
    assert second["model_calls"] == len(calls) > first["model_calls"]
