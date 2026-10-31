# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Dynamic agent generation: plateau detection, spawn/retire, orchestrator wiring."""

from __future__ import annotations

from types import SimpleNamespace

from evoalgo import specialists
from evoalgo.config import Bound, RunConfig
from evoalgo.events import read_events
from evoalgo.orchestrator import Orchestrator


def committed(gen, fitness, wr, best="b"):
    return {"type": "gen_committed", "gen": gen, "best_fitness": fitness,
            "best_work_ratio": wr, "best_id": best}


def cfg(**kw):
    base = dict(plateau_window=2, plateau_epsilon=0.01, agent_budget=1, specialist_generations=2)
    return SimpleNamespace(**(base | kw))


def test_plateau_on_fitness_or_work_ratio():
    flat = [committed(g, 1.0, 0.5) for g in (1, 2, 3)]
    assert specialists.plateaued(specialists.best_history(flat), 2, 0.01)
    cheaper = [committed(1, 1.0, 0.5), committed(2, 1.0, 0.5), committed(3, 1.0, 0.45)]
    assert not specialists.plateaued(specialists.best_history(cheaper), 2, 0.01)
    fitter = [committed(1, 0.5, 0.5), committed(2, 0.5, 0.5), committed(3, 0.9, 0.5)]
    assert not specialists.plateaued(specialists.best_history(fitter), 2, 0.01)
    assert not specialists.plateaued(specialists.best_history(flat[:2]), 2, 0.01)  # too short


def test_spawn_signature_and_retire():
    events = [committed(g, 1.0, 0.5) for g in (1, 2, 3)]
    acts = specialists.boundary_actions(events, 3, cfg())
    assert [a[0] for a in acts] == ["plateau_detected", "agent_spawned"]
    spawn = acts[1][1]
    assert spawn["kind"] == "efficiency" and spawn["agent"] == "specialist-1"
    assert "work ratio 0.500" in spawn["focus"]
    events.append({"type": "agent_spawned", **spawn})
    # Budget of one active specialist: no second spawn while it is active.
    assert specialists.boundary_actions(events + [committed(4, 1.0, 0.5)], 4, cfg()) == []
    # Retired after its generation budget (2 candidates).
    for i in (1, 2):
        events.append({"type": "candidate_generated", "id": f"s{i}", "gen": 3 + i,
                       "role": "specialist", "agent": "specialist-1"})
        events.append(committed(3 + i, 1.0, 0.5))
    acts = specialists.boundary_actions(events, 5, cfg())
    assert acts[0] == ("agent_retired", {"gen": 5, "agent": "specialist-1",
                                         "reason": "generation_budget", "candidates": 2,
                                         "gained": False})


def test_gain_is_credited_and_correctness_signature():
    events = [{"type": "agent_spawned", "gen": 1, "agent": "specialist-1", "focus": "f"},
              {"type": "candidate_generated", "id": "s1", "gen": 2, "role": "specialist",
               "agent": "specialist-1"},
              committed(2, 1.0, 0.4, best="s1")]
    (spec,) = specialists.specialists(events)
    assert spec.produced == ["s1"] and spec.last_gain_gen == 2
    failing = [committed(g, 0.5, 0.9) for g in (1, 2, 3)] + [
        {"type": "candidate_verified", "gen": 3, "state": "FAIL",
         "failing_case": {"operation": "delete (1, 2)", "graph_n": 4}}]
    kind, sig = specialists.signature(failing, 1, specialists.best_history(failing))
    assert kind == "correctness" and "'delete'" in sig


def test_mock_run_spawns_and_retires_a_specialist(tmp_path):
    config = RunConfig(problem="dynamic_bfs", provider="mock", population_size=2,
                       max_generations=8, elitism_k=1, early_stop_on_success=False,
                       dynamic_agents=True, plateau_window=2, agent_budget=1,
                       specialist_generations=2,
                       bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                       search_n_max=2, search_seq_count=1, final_grade=False,
                       workdir=str(tmp_path))
    Orchestrator(config, run_id="dyn").run()
    events = read_events(tmp_path / "dyn")
    kinds = [e["type"] for e in events]
    assert "plateau_detected" in kinds and "agent_spawned" in kinds and "agent_retired" in kinds
    spawns = [e for e in events if e["type"] == "agent_spawned"]
    retires = {e["agent"]: e for e in events if e["type"] == "agent_retired"}
    made = [e for e in events if e["type"] == "candidate_generated" and e.get("role") == "specialist"]
    calls = [e for e in events if e["type"] == "agent_call_start" and e["role"] == "specialist"]
    assert [c["agent"] for c in calls] == [m["agent"] for m in made]
    first = spawns[0]
    own = [m for m in made if m["agent"] == first["agent"]]
    # One candidate per generation after the spawn, retired after its budget of 2.
    assert [m["gen"] for m in own] == [first["gen"] + 1, first["gen"] + 2]
    assert retires[first["agent"]]["reason"] == "generation_budget"
    # Budget of one active specialist: a later one spawns only after the first retired.
    for later in spawns[1:]:
        assert later["gen"] >= retires[first["agent"]]["gen"]


def test_focus_is_in_the_task_message(tmp_path):
    from evoalgo.agents.base import Task
    from evoalgo.agents.prompts import task_message
    task = Task(role="generate", candidate_id="gen004_c03", problem="dynamic_bfs",
                problem_prompt="PROBLEM: dynamic_bfs", run_dir=tmp_path, parent_code="x = 1",
                focus="Concentrate on deletes.")
    msg = task_message(task, False)
    assert "SPECIALIST FOCUS:\nConcentrate on deletes." in msg
    assert "SPECIALIST FOCUS" not in task_message(
        Task(role="generate", candidate_id="c", problem="dynamic_bfs", problem_prompt="P",
             run_dir=tmp_path), False)


def test_disabled_by_default(tmp_path):
    config = RunConfig(problem="dynamic_bfs", provider="mock", population_size=2,
                       max_generations=4, elitism_k=1, early_stop_on_success=False,
                       plateau_window=1,
                       bound=Bound(n_max=3, n_random=0, seq_len_max=2, seq_count=1, seed=1),
                       search_n_max=2, search_seq_count=1, final_grade=False,
                       workdir=str(tmp_path))
    Orchestrator(config, run_id="off").run()
    assert not any(e["type"] in ("plateau_detected", "agent_spawned")
                   for e in read_events(tmp_path / "off"))


def test_signature_without_failure_records_is_still_correctness():
    events = [committed(g, 0.8, 0.9) for g in (1, 2, 3)]
    kind, _ = specialists.signature(events, 1, specialists.best_history(events))
    assert kind == "correctness"


def test_redone_generation_counts_specialist_candidates_once():
    from evoalgo.specialists import specialists
    ev = [{"type": "agent_spawned", "agent": "s1", "focus": "f", "gen": 2},
          {"type": "candidate_generated", "role": "specialist", "agent": "s1", "id": "gen003_c01"},
          # crash before gen 3's checkpoint; resume regenerates the same id
          {"type": "candidate_generated", "role": "specialist", "agent": "s1", "id": "gen003_c01"}]
    assert specialists(ev)[0].produced == ["gen003_c01"]
