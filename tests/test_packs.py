# AI-assisted code: generated and revised with Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Tests for problem packs: loading, validation, config resolution, prompt
brief inclusion, and verifier update_mode filtering.

These cover the generic research-tooling contract: a researcher describes a
problem with a folder (problem.yaml + brief.md), the config resolves the
checker from the pack, the brief lands in the agent prompt, and the verifier
honours the pack's update_mode.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from evoalgo.config import RunConfig, VALID_PROBLEMS
from evoalgo.llm_provider import LLMProvider
from evoalgo.packs import (
    DEFAULT_PROBLEMS_ROOT,
    PackError,
    find_packs,
    load_pack,
    resolve_pack,
)
from evoalgo.problem_definitions import get_problem
from evoalgo.sandbox import Sandbox
from evoalgo.verifier import Verifier

REPO = Path(__file__).resolve().parents[1]

# The six shipped packs, and the checker each must resolve to.
SHIPPED = {
    "dynamic_bfs": ("dynamic_bfs", "calibration"),
    "dynamic_dfs": ("dynamic_dfs", "calibration"),
    "dynamic_scc": ("dynamic_scc", "core"),
    "reachability": ("reachability", "core"),
    "dynamic_mcs": ("dynamic_mcs", "core"),
    "dynamic_lbfs": ("dynamic_lbfs", "open"),
}


# -- shipped packs -----------------------------------------------------------

def test_all_shipped_packs_load():
    for name, (checker, tier) in SHIPPED.items():
        pack = load_pack(DEFAULT_PROBLEMS_ROOT / name)
        assert pack.name == name
        assert pack.checker == checker
        assert pack.tier == tier
        assert pack.brief.strip(), f"{name}: brief.md must be non-empty"
        # directed/needs_root must match the built-in checker's flags
        ref = get_problem(checker)
        assert pack.directed == ref.directed
        assert pack.needs_root == ref.needs_root


def test_find_packs_discovers_all_shipped():
    found = {p.name for p in find_packs(DEFAULT_PROBLEMS_ROOT)}
    assert set(SHIPPED) <= found


def test_resolve_pack_by_name_and_by_path():
    by_name = resolve_pack("dynamic_mcs")
    by_path = resolve_pack(DEFAULT_PROBLEMS_ROOT / "dynamic_mcs")
    assert by_name.name == by_path.name == "dynamic_mcs"
    with pytest.raises(PackError):
        resolve_pack("no_such_pack")


# -- validation errors -------------------------------------------------------

def _write_pack(tmp_path: Path, name: str = "myproblem", **overrides) -> Path:
    """Write a minimal valid pack, then apply overrides to problem.yaml."""
    base = {
        "name": name,
        "title": "A test problem",
        "directed": True,
        "needs_root": True,
        "checker": "dynamic_bfs",
        "tier": "calibration",
        "objective": {"primary": "correctness", "then": "efficiency"},
        "update_mode": "mixed",
        "lean": {"enabled": False},
    }
    base.update(overrides)
    d = tmp_path / name
    d.mkdir()
    import yaml
    (d / "problem.yaml").write_text(yaml.dump(base))
    (d / "brief.md").write_text("Research question: does it work?\n")
    return d


def test_missing_brief_rejected(tmp_path):
    d = _write_pack(tmp_path)
    (d / "brief.md").unlink()
    with pytest.raises(PackError) as e:
        load_pack(d)
    assert any("brief.md" in m for m in e.value.errors)


def test_unknown_key_rejected(tmp_path):
    import yaml
    d = _write_pack(tmp_path)
    data = yaml.safe_load((d / "problem.yaml").read_text())
    data["bogus_key"] = 1
    (d / "problem.yaml").write_text(yaml.dump(data))
    with pytest.raises(PackError) as e:
        load_pack(d)
    assert any("unknown key" in m and "bogus_key" in m for m in e.value.errors)


def test_unknown_checker_rejected(tmp_path):
    d = _write_pack(tmp_path, checker="not_a_checker")
    with pytest.raises(PackError) as e:
        load_pack(d)
    assert any("unknown checker" in m for m in e.value.errors)


def test_flag_mismatch_rejected(tmp_path):
    # dynamic_bfs is directed+rooted; declaring it undirected must fail.
    d = _write_pack(tmp_path, directed=False)
    with pytest.raises(PackError) as e:
        load_pack(d)
    assert any("directed" in m for m in e.value.errors)


def test_name_folder_mismatch_rejected(tmp_path):
    # Folder is "myproblem" but the yaml declares name "other_name".
    d = _write_pack(tmp_path, name="myproblem")
    import yaml
    data = yaml.safe_load((d / "problem.yaml").read_text())
    data["name"] = "other_name"
    (d / "problem.yaml").write_text(yaml.dump(data))
    with pytest.raises(PackError) as e:
        load_pack(d)
    assert any("match the pack folder name" in m for m in e.value.errors)


def test_multiple_errors_listed_together(tmp_path):
    d = _write_pack(tmp_path, checker="nope", tier="bogus")
    (d / "brief.md").unlink()
    with pytest.raises(PackError) as e:
        load_pack(d)
    # All three problems reported at once, not just the first.
    assert any("unknown checker" in m for m in e.value.errors)
    assert any("tier" in m for m in e.value.errors)
    assert any("brief.md" in m for m in e.value.errors)


# -- config resolution -------------------------------------------------------

def test_valid_problems_includes_lbfs():
    assert "dynamic_lbfs" in VALID_PROBLEMS


def test_config_with_pack_resolves_problem(tmp_path):
    cfg = RunConfig(problem="dynamic_mcs", pack="dynamic_scc")
    errors = cfg.validate()
    assert errors == [], errors
    assert cfg.problem == "dynamic_scc"  # pack overrides the stale problem


def test_config_old_style_still_works():
    cfg = RunConfig(problem="dynamic_bfs")
    assert cfg.validate() == []
    assert cfg.problem == "dynamic_bfs"


def test_config_with_bad_pack_reports_error(tmp_path):
    cfg = RunConfig(problem="dynamic_mcs", pack="no_such_pack")
    errors = cfg.validate()
    assert any("no problem pack found" in e for e in errors)


def test_config_pack_and_problem_round_trip(tmp_path):
    cfg = RunConfig(problem="dynamic_mcs", pack="dynamic_mcs")
    cfg.validate()
    d = cfg.to_dict()
    assert d["pack"] == "dynamic_mcs"
    assert d["problem"] == "dynamic_mcs"


def test_bad_config_files_give_one_line_errors(tmp_path, capsys):
    from evoalgo.cli import main
    cases = {
        "missing.yaml": None,
        "syntax.yaml": "x: [\n",
        "list.yaml": "- 1\n- 2\n",
        "bound.yaml": "bound: 5\n",
        "types.yaml": "population_size: '8'\nbound:\n  n_max: 5.5\n",
    }
    expected = {
        "missing.yaml": "cannot read config",
        "syntax.yaml": "is not valid YAML: expected the node content, but found '<stream end>' (line 2, column 1)",
        "list.yaml": "must be a mapping",
        "bound.yaml": "'bound' must be a mapping",
        "types.yaml": "population_size must be an integer",
    }
    for name, text in cases.items():
        if text is not None:
            (tmp_path / name).write_text(text)
        assert main(["start", str(tmp_path / name)]) == 1, name
        out = capsys.readouterr()
        assert expected[name] in out.out + out.err, (name, out)
        assert "Traceback" not in out.out + out.err, name


def test_corrupt_run_dir_is_reported_not_raised(tmp_path, capsys):
    from evoalgo.cli import main
    run = tmp_path / "r"
    run.mkdir()
    RunConfig(problem="dynamic_bfs", provider="mock").save(run / "config.yaml")
    (run / "COMMITTED").write_text("1")
    (run / "generation_0001.json").write_text("{not json")
    for cmd in ("status", "export", "resume"):
        assert main([cmd, str(run)]) == 1, cmd
        assert "generation_0001.json" in capsys.readouterr().err, cmd
    (run / "COMMITTED").write_text("junk")
    assert main(["status", str(run)]) == 1
    assert "corrupt marker" in capsys.readouterr().err


# -- prompt brief inclusion --------------------------------------------------

def test_prompt_contains_pack_brief(tmp_path):
    cfg = RunConfig(problem="dynamic_mcs", pack="dynamic_mcs")
    cfg.validate()
    provider = LLMProvider(config=cfg, run_dir=tmp_path)
    prompt = provider._build_problem_prompt("dynamic_mcs")
    assert "RESEARCH BRIEF:" in prompt
    # A distinctive line from the shipped MCS brief must be present verbatim.
    assert "perfect elimination ordering" in prompt


def test_prompt_without_pack_has_no_brief(tmp_path):
    cfg = RunConfig(problem="dynamic_mcs")
    provider = LLMProvider(config=cfg, run_dir=tmp_path)
    prompt = provider._build_problem_prompt("dynamic_mcs")
    assert "RESEARCH BRIEF:" not in prompt


def test_prompt_keeps_researcher_hint(tmp_path):
    cfg = RunConfig(problem="dynamic_mcs", pack="dynamic_mcs")
    cfg.validate()
    provider = LLMProvider(config=cfg, run_dir=tmp_path)
    provider.hint = "try a cardinality bucket"
    prompt = provider._build_problem_prompt("dynamic_mcs")
    assert "RESEARCH BRIEF:" in prompt
    assert "RESEARCHER HINT: try a cardinality bucket" in prompt


# -- verifier update_mode ----------------------------------------------------

def _graph_with_edges(n: int, edges) -> np.ndarray:
    g = np.zeros((n, n), dtype=int)
    for u, v in edges:
        g[u, v] = 1
    return g


def _verifier_for_mode(mode: str) -> Verifier:
    problem = get_problem("dynamic_bfs")
    sandbox = Sandbox(timeout_seconds=5, directed=problem.directed)
    return Verifier(
        problem=problem,
        sandbox=sandbox,
        bound_n_max=2,
        bound_n_random=0,
        bound_seq_len_max=10,
        bound_seq_count=4,
        bound_seed=42,
        use_offline=False,
        relabels_per_class=0,
        workers=1,
        update_mode=mode,
    )


def test_update_mode_mixed_unchanged():
    v = _verifier_for_mode("mixed")
    g = _graph_with_edges(2, [(0, 1)])
    seqs = v.get_sequences(2, g)
    ops = {op for seq in seqs for op, _ in seq}
    assert "insert" in ops and "delete" in ops


def test_update_mode_insert_only():
    v = _verifier_for_mode("insert_only")
    # A graph with one absent edge (1,0) so inserts are possible.
    g = _graph_with_edges(2, [(0, 1)])
    seqs = v.get_sequences(2, g)
    ops = {op for seq in seqs for op, _ in seq}
    assert ops <= {"insert"}, ops
    # At least one sequence must actually contain an insert.
    assert any(op == "insert" for seq in seqs for op, _ in seq)


def test_update_mode_delete_only():
    v = _verifier_for_mode("delete_only")
    # A graph with an edge so deletes are possible.
    g = _graph_with_edges(2, [(0, 1), (1, 0)])
    seqs = v.get_sequences(2, g)
    ops = {op for seq in seqs for op, _ in seq}
    assert ops <= {"delete"}, ops
    assert any(op == "delete" for seq in seqs for op, _ in seq)


def test_update_mode_invalid_raises():
    problem = get_problem("dynamic_bfs")
    sandbox = Sandbox(timeout_seconds=5, directed=problem.directed)
    with pytest.raises(ValueError):
        Verifier(problem=problem, sandbox=sandbox, update_mode="sideways")


def test_update_mode_sequences_stay_legal():
    # Replaying a filtered sequence on the base graph must never try to insert
    # an edge that is present or delete one that is absent.
    v = _verifier_for_mode("insert_only")
    g = _graph_with_edges(3, [(0, 1), (1, 2)])
    for seq in v.get_sequences(3, g):
        cur = g.copy()
        for op, (u, w) in seq:
            if op == "insert":
                assert cur[u, w] == 0
                cur[u, w] = 1
            else:
                assert cur[u, w] == 1
                cur[u, w] = 0
