# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tests for the agent layer: tools, api tool loop, mock backend, wiring."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from evoalgo.agents.api import ApiBackend
from evoalgo.agents.base import CallResult, Task, make_backend
from evoalgo.agents.examples import PUBLIC_N_MAX, run_examples
from evoalgo.agents.harness import OpencodeBackend
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
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.requests.append({**kw, "messages": [dict(m) for m in kw["messages"]]})
        content, calls = self.turns.pop(0)
        tcs = [SimpleNamespace(id=f"t{i}", function=SimpleNamespace(name=n, arguments=json.dumps(a))) for i, (n, a) in enumerate(calls)]
        msg = SimpleNamespace(content=content, tool_calls=tcs or None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="tool_calls" if tcs else "stop")],
                  usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20))


def api_config(**kw):
    return RunConfig(problem="dynamic_bfs", provider="api", api_base_url="openrouter", model="m", **kw)


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
        chat = SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: (_ for _ in ()).throw(RuntimeError("503"))))
    r = ApiBackend(api_config(), tmp_path, client=Boom()).run(task(tmp_path))
    assert not r.ok and "503" in r.error


def test_api_thinking_off_and_length_nudge(tmp_path):
    class LengthThenWrite(ScriptedClient):
        def _create(self, **kw):
            if not self.requests:  # a reasoning model burning the whole budget
                self.requests.append({**kw, "messages": [dict(m) for m in kw["messages"]]})
                msg = SimpleNamespace(content="", tool_calls=None)
                return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason="length")], usage=None)
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
    assert d["api_base_url"] == "openrouter" and d["agent_max_steps"] == 7 and "bound" in d


def test_opencode_command_and_parse(tmp_path):
    cfg = RunConfig(problem="dynamic_bfs", provider="opencode", model="openrouter/x", harness_bin="/bin/oc")
    b = OpencodeBackend(cfg, tmp_path)
    cmd = b.command(task(tmp_path, role="repair"), "PROMPT")
    assert cmd[:2] == ["/bin/oc", "run"] and ["--agent", "algorithm-repairer"] == cmd[cmd.index("--agent"):cmd.index("--agent") + 2]
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


def test_unusable_backend_stops_after_seeding(tmp_path):
    class Broken:
        def run(self, task):
            return CallResult(ok=False, error="harness binary not found: /x/opencode")
    cfg = RunConfig(problem="dynamic_bfs", provider="mock", population_size=2, max_generations=5,
                    elitism_k=1, bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                    search_n_max=2, search_seq_count=1, workdir=str(tmp_path))
    orch = Orchestrator(cfg, run_id="b")
    orch.provider.backend = Broken()
    summary = orch.run()
    assert summary["stop_reason"] == "agent_unavailable" and summary["generation"] == 1
    assert summary["model_calls"] == 2
    assert "binary not found" in summary["agent_error"]
    failed = [e for e in read_events(tmp_path / "b") if e["type"] == "agent_failed"]
    assert [e["error"] for e in failed] == ["harness binary not found: /x/opencode"] * 2
    # Resumed with the backend still broken: it stops again after one generation.
    orch = Orchestrator(cfg, run_id="b")
    orch.provider.backend = Broken()
    again = orch.run()
    assert again["stop_reason"] == "agent_unavailable" and again["generation"] == 2
    assert again["model_calls"] == 4
    # Once the backend works, resume continues the run.
    resumed = Orchestrator(cfg, run_id="b").run()
    assert resumed["stop_reason"] != "agent_unavailable" and resumed["best_fitness"] == 1.0


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



def _gen_parents(run_dir, gen):
    return [(e["id"], e.get("parent_ids")) for e in read_events(run_dir)
            if e["type"] == "candidate_generated" and e.get("gen") == gen]


def test_resume_draws_the_same_selection_stream(tmp_path):
    """Parent selection in a generation must not depend on whether the run
    was interrupted before it."""
    base = dict(problem="dynamic_bfs", provider="mock", population_size=3, elitism_k=1,
                early_stop_on_success=False, mock_script=["bad"] * 40, model_call_budget=100,
                bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                search_n_max=2, search_seq_count=1, workdir=str(tmp_path), selection_seed=7)
    Orchestrator(RunConfig(max_generations=3, **base), run_id="a").run()
    Orchestrator(RunConfig(max_generations=1, **base), run_id="b").run()
    Orchestrator(RunConfig(max_generations=3, **base), run_id="b").run()
    for gen in (2, 3):
        assert _gen_parents(tmp_path / "a", gen) == _gen_parents(tmp_path / "b", gen)


def test_resume_counts_calls_of_a_crashed_generation(tmp_path):
    """Calls logged after the last checkpoint (a crash mid-generation) stay
    spent after a resume."""
    base = dict(problem="dynamic_bfs", provider="mock", population_size=2, elitism_k=1,
                early_stop_on_success=False, mock_script=["bad"] * 20, model_call_budget=100,
                bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                search_n_max=2, search_seq_count=1, workdir=str(tmp_path))
    Orchestrator(RunConfig(max_generations=1, **base), run_id="r").run()
    from evoalgo.events import EventLog
    log = EventLog(tmp_path / "r")
    for i in range(3):  # three calls of a generation that never committed
        log.emit("agent_call_start", gen=2, role="mutate", id=f"gen002_c0{i + 1}")
    orch = Orchestrator(RunConfig(max_generations=1, **base), run_id="r")
    assert orch._try_resume()
    starts = sum(e["type"] == "agent_call_start" for e in read_events(tmp_path / "r"))
    assert orch.model_calls == orch.provider.call_count == starts

def test_api_error_text_drops_response_body():
    from evoalgo.agents.api import _safe_error

    class AuthenticationError(Exception):
        status_code = 401
        body = {"message": "Incorrect API key provided: sk-abc...wxyz", "code": "invalid_api_key"}

    text = _safe_error(AuthenticationError("Error code: 401 - Incorrect API key provided: sk-abc...wxyz"))
    assert text == "AuthenticationError (HTTP 401, invalid_api_key)" and "sk-" not in text
    assert _safe_error(TimeoutError("read timed out")) == "TimeoutError: read timed out"


FAKE_OPENCODE = r'''#!/bin/sh
# Stand-in for opencode: probes what an agent with a shell can reach (paths
# from OPENCODE_* variables, which the harness passes on), then leaves its
# output file in the run directory it was started in.
{
  for f in "$OPENCODE_VERIFIER" "$OPENCODE_TESTFILE"; do
    if [ -r "$f" ]; then echo "read $f"; fi
    if [ -w "$f" ]; then echo "write $f"; fi
  done
  if [ -e "$OPENCODE_PRIOR" ]; then echo "see $OPENCODE_PRIOR"; fi
  if cat /proc/[0-9]*/environ 2>/dev/null | tr '\0' '\n' | grep -q EVOALGO_TEST_KEY; then echo "key"; fi
} > "$OPENCODE_PROBE"
ln -s "$OPENCODE_VERIFIER" candidates/escape.py 2>/dev/null || :
if [ -n "$OPENCODE_HARDLINK" ]; then
  ln "$OPENCODE_HARDLINK" candidates/gen001_c01.py
else
  printf 'def init(g): return {}\n' > candidates/gen001_c01.py
fi
'''


@pytest.mark.parametrize("run_in_repo", [False, True])
def test_harness_agent_cannot_reach_trusted_code(tmp_path, monkeypatch, run_in_repo):
    """The opencode backend's process is jailed: it can write its output file
    but cannot read or change the verifier or the tests, see the rest of the
    run, or read the engine's environment; a symlink it leaves is not
    followed back into the run. Also when the run directory is inside the
    hidden checkout (the default runs/ of a source install)."""
    import os
    from pathlib import Path
    import evoalgo
    from evoalgo import sandbox
    from evoalgo.agents import harness
    if os.environ.get(sandbox.JAIL_ENV) == "none":
        pytest.skip("jail disabled")
    if run_in_repo:
        real = harness.hidden_from_agents
        monkeypatch.setattr(harness, "hidden_from_agents", lambda: real() + [str(tmp_path / "repo")])
    probe = tmp_path / "probe" / "out.txt"
    probe.parent.mkdir()
    fake = tmp_path / "bin" / "opencode"
    fake.parent.mkdir()
    fake.write_text(FAKE_OPENCODE)
    fake.chmod(0o755)
    verifier_src = Path(evoalgo.__file__).parent / "verifier.py"
    before = verifier_src.read_bytes()
    run = tmp_path / "repo" / "runs" / "r" if run_in_repo else tmp_path / "run"
    run.mkdir(parents=True)
    t = task(run)
    (run / "candidates" / "gen000_c01.py").write_text("prior = 1\n")
    monkeypatch.setenv("EVOALGO_TEST_KEY", "x")  # like an API key in the engine's environment
    for name, value in {"VERIFIER": verifier_src, "TESTFILE": Path(__file__),
                        "PRIOR": run / "candidates" / "gen000_c01.py", "PROBE": probe}.items():
        monkeypatch.setenv(f"OPENCODE_{name}", str(value))
    cfg = RunConfig(problem="dynamic_bfs", provider="opencode", harness_bin=str(fake))
    result = OpencodeBackend(cfg, run).run(t)
    assert result.ok, result.error
    assert probe.read_text() == ""
    assert (run / "candidates" / "gen001_c01.py").read_text() == "def init(g): return {}\n"
    assert not (run / "candidates" / "escape.py").exists()
    assert verifier_src.read_bytes() == before
    assert not list((run / ".agent").iterdir())  # the work directory is removed

    # An output that is a hard link to another file of the user is not taken.
    other = tmp_path / "probe" / "users_file"
    other.write_text("not a candidate\n")
    monkeypatch.setenv("OPENCODE_HARDLINK", str(other))
    (run / "candidates" / "gen001_c01.py").unlink()
    result = OpencodeBackend(cfg, run).run(t)
    assert not result.ok and not (run / "candidates" / "gen001_c01.py").exists()


PLANTING_OPENCODE = r'''#!/bin/sh
# Plants fake jail tools in a directory on its own PATH (the user's home is
# writable from the jail), then records whether the verifier is reachable.
for t in unshare sh mount; do
  printf '#!/bin/sh\necho planted >> "$OPENCODE_PROBE"\nexec /usr/bin/%s "$@"\n' "$t" > "$OPENCODE_PLANT/$t"
  chmod +x "$OPENCODE_PLANT/$t"
done
if [ -r "$OPENCODE_VERIFIER" ]; then echo "read" >> "$OPENCODE_PROBE"; fi
# Sockets of the user's tmux and session bus would run commands unjailed.
if [ -n "$(ls -A /tmp)" ]; then echo "tmp" >> "$OPENCODE_PROBE"; fi
if [ -n "$(ls -A "/run/user/$(id -u)" 2>/dev/null)" ]; then echo "run" >> "$OPENCODE_PROBE"; fi
printf 'def init(g): return {}\n' > candidates/gen001_c01.py
'''


def test_agent_cannot_plant_jail_tools_on_its_path(tmp_path, monkeypatch):
    """A tool the agent leaves on its PATH is not used to build the next
    jail: the jail's own unshare, sh and mount come from the system PATH."""
    import os
    from pathlib import Path
    import evoalgo
    from evoalgo import sandbox
    if os.environ.get(sandbox.JAIL_ENV) == "none":
        pytest.skip("jail disabled")
    plant, probe = tmp_path / "plant", tmp_path / "probe"
    plant.mkdir()
    probe.write_text("")
    fake = tmp_path / "bin" / "opencode"
    fake.parent.mkdir()
    fake.write_text(PLANTING_OPENCODE)
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{plant}:{os.environ['PATH']}")
    for name, value in {"PLANT": plant, "PROBE": probe,
                        "VERIFIER": Path(evoalgo.__file__).parent / "verifier.py"}.items():
        monkeypatch.setenv(f"OPENCODE_{name}", str(value))
    run = tmp_path / "run"
    run.mkdir()
    cfg = RunConfig(problem="dynamic_bfs", provider="opencode", harness_bin=str(fake))
    for _ in range(2):  # the second call would start from the planted tools
        assert OpencodeBackend(cfg, run).run(task(run)).ok
    assert probe.read_text() == ""
    # A library planted on its LD_LIBRARY_PATH would be loaded by the inner
    # unshare, which can still unmount; a broken libc there must not matter.
    (plant / "libc.so.6").write_text("not a library")
    monkeypatch.setenv("LD_LIBRARY_PATH", str(plant))
    monkeypatch.setenv("OPENCODE_PLANT", str(tmp_path / "unused"))
    (tmp_path / "unused").mkdir()
    err = OpencodeBackend(cfg, run).run(task(run)).error or ""
    # The agent's own command may load it (it runs as the user); the jail's
    # unshare and env must not.
    assert "unshare: error while loading" not in err and "env: error while loading" not in err


def test_lean_checks_run_jailed(tmp_path, monkeypatch):
    """lake runs the agent-written Lean project (lakefile and #eval code run at
    build time), so the formalize checks run in the agent jail as well."""
    import os
    from pathlib import Path
    import evoalgo
    from evoalgo import formalize, sandbox
    if os.environ.get(sandbox.JAIL_ENV) == "none":
        pytest.skip("jail disabled")
    project, probe, bindir = tmp_path / "lean", tmp_path / "probe", tmp_path / "bin"
    project.mkdir()
    bindir.mkdir()
    (bindir / "lake").write_text('#!/bin/sh\nif [ -r "$OPENCODE_VERIFIER" ]; then echo read > "$OPENCODE_PROBE"; fi\n'
                                 'echo "Build completed successfully"\n')
    (bindir / "lake").chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    monkeypatch.setenv("OPENCODE_VERIFIER", str(Path(evoalgo.__file__).parent / "verifier.py"))
    monkeypatch.setenv("OPENCODE_PROBE", str(probe))
    proc = formalize._lake(project, ["build", "X"], 60)
    assert proc.returncode == 0 and "Build completed" in proc.stdout
    assert not probe.exists()


def test_harness_env_is_allow_listed(monkeypatch):
    from evoalgo.agents.harness import harness_env
    monkeypatch.setenv("GERRIT_PASSWORD", "x")
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("OPENCODE_CONFIG", "/cfg")
    env = harness_env("opencode", TMPDIR="/scratch")
    assert "GERRIT_PASSWORD" not in env and "OPENROUTER_API_KEY" not in env
    assert env["OPENCODE_CONFIG"] == "/cfg" and env["TMPDIR"] == "/scratch" and "HOME" in env


def test_agy_backend_command_parse_and_env(tmp_path, monkeypatch):
    from evoalgo.agents import make_backend
    from evoalgo.agents.base import Task
    from evoalgo.agents.harness import AgyBackend, harness_env
    from evoalgo.config import RunConfig

    cfg = RunConfig(pack="dynamic_bfs", problem="dynamic_bfs", provider="agy",
                    model="gemini-3.8-flash", agent_max_seconds=90, harness_bin="/usr/bin/agy")
    assert cfg.validate() == []
    backend = make_backend(cfg, tmp_path)
    assert isinstance(backend, AgyBackend)
    task = Task(role="generate", candidate_id="gen001_c01", problem="dynamic_bfs",
                problem_prompt="P", run_dir=tmp_path)
    cmd = backend.command(task, "PROMPT")
    assert cmd[:2] == ["/usr/bin/agy", "-p"]
    assert "--output-format" in cmd and "json" in cmd
    assert "--model" in cmd and "gemini-3.8-flash" in cmd
    assert cmd[-1] == "PROMPT"

    summary, usage = backend.parse('{"result": "done", "usage": {"input_tokens": 12, "output_tokens": 34}}')
    assert summary == "done" and usage == {"prompt_tokens": 12, "completion_tokens": 34}

    monkeypatch.setenv("ANTIGRAVITY_HOME", "/agy")
    monkeypatch.setenv("UNRELATED_SECRET", "nope")
    env = harness_env("agy")
    assert env["ANTIGRAVITY_HOME"] == "/agy" and "UNRELATED_SECRET" not in env
