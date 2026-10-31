# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Harness workspaces: one coding agent (Claude Code, Codex, opencode) runs the
search loop itself, autoresearch-style, and evoalgo only grades and records.

``evoalgo init <pack> [dir]`` creates a run folder under ``runs/`` with
``program.md`` (the agent's instructions), ``candidate.py`` (the one file the
agent edits) and ``results.tsv``. ``evoalgo check`` grades candidate.py,
stores a hashed snapshot under ``candidates/``, appends to ``results.tsv`` and writes
the usual events, so the web UI shows the session like any other run (one
check = one generation).

The grades are visible to the agent; what counts for evaluation is
``evoalgo check --final``, our independent re-grade of the kept candidate.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shutil
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .candidate import Candidate
from .config import RunConfig
from .events import EventLog, read_events
from .packs import resolve_pack
from .problem_definitions import get_problem
from .sandbox import Sandbox
from .verifier import Verifier

WORKSPACE_FILE = "workspace.json"
PROGRAM_FILE = "program.md"
CANDIDATE_FILE = "candidate.py"
RESULTS_FILE = "results.tsv"
# In the run folder: marks a harness-driven run (evoalgo resume refuses it).
HARNESS_MARKER = "HARNESS"
RESULTS_HEADER = "check\tcandidate_id\tlevel\tverdict\tpassed\ttotal\twork_ratio\tseconds\tnote\n"

# Grade levels, cheapest first. "search" matches the orchestrator's search
# grade, "full" its final grade (the run config's bound).
LEVELS = ("examples", "search", "full")

_STARTER = '''"""Dynamic algorithm candidate. Edit this file; keep the three functions."""


def init(graph):
    raise NotImplementedError


def insert_edge(graph, edge, state):
    raise NotImplementedError


def delete_edge(graph, edge, state):
    raise NotImplementedError
'''


@dataclass
class Workspace:
    dir: Path
    run_dir: Path
    pack: str
    problem: str

    @classmethod
    def find(cls, start: Path | str = ".") -> "Workspace":
        """The workspace containing ``start`` (walks up like git)."""
        p = Path(start).resolve()
        for d in [p, *p.parents] if p.is_dir() else [p.parent, *p.parent.parents]:
            f = d / WORKSPACE_FILE
            if f.is_file():
                info = json.loads(f.read_text())
                return cls(dir=d, run_dir=Path(info["run_dir"]), pack=info["pack"],
                           problem=info["problem"])
        raise FileNotFoundError(f"no {WORKSPACE_FILE} in {p} or its parents; run `evoalgo init <pack>` first")


def init_workspace(pack_name: str, target: Path | str | None = None,
                   runs_root: Path | str = "runs", run_id: str | None = None,
                   goal: str | None = None, harness: str | None = None,
                   max_checks: int | None = None) -> Workspace:
    """Create the run folder and the files the agent works with.

    ``target`` defaults to the run folder itself; another directory (e.g. a
    fresh git repo) gets the agent files, and the run folder stays under
    ``runs_root`` so the UI finds it.
    """
    pack = resolve_pack(pack_name)
    run_id = run_id or time.strftime(f"harness_{pack.name}_%Y%m%d_%H%M%S")
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$", run_id):
        raise ValueError("run id may only contain letters, digits, '.', '_', '-'")
    run_dir = Path(runs_root).resolve() / run_id
    if run_dir.exists():
        raise FileExistsError(f"run {run_dir} already exists")
    ws_dir = Path(target).resolve() if target else run_dir
    for name in (WORKSPACE_FILE, PROGRAM_FILE, CANDIDATE_FILE, RESULTS_FILE):
        if (ws_dir / name).exists():
            raise FileExistsError(f"{ws_dir / name} exists; pick an empty directory")

    # provider stays a valid value: the orchestrator never drives this run;
    # the coding agent does, and the run_start event records which one.
    config = RunConfig(pack=pack.name, problem=pack.checker, provider="mock",
                       model=harness, research_goal=(goal or "").strip() or None,
                       population_size=1, max_generations=1000, elitism_k=0,
                       max_checks=max_checks, workdir=str(run_dir.parent))
    errors = [e for e in config.validate() if "max_checks" in e]
    if errors:
        raise ValueError(errors[0])
    program = program_text(pack, config.research_goal, max_checks)
    agent_files = {
        WORKSPACE_FILE: json.dumps({"run_dir": str(run_dir), "pack": pack.name,
                                    "problem": pack.checker}, indent=2) + "\n",
        PROGRAM_FILE: program, CANDIDATE_FILE: _STARTER, RESULTS_FILE: RESULTS_HEADER,
    }
    run_dir.mkdir(parents=True)
    written: list[Path] = []
    try:
        (run_dir / "candidates").mkdir()
        config.save(run_dir / "config.yaml")
        (run_dir / HARNESS_MARKER).write_text(str(ws_dir) + "\n")
        ws_dir.mkdir(parents=True, exist_ok=True)
        for name, text in agent_files.items():
            (ws_dir / name).write_text(text)
            written.append(ws_dir / name)
        EventLog(run_dir).emit(
            "run_start", run_id=run_id, problem=pack.checker, pack=pack.name,
            research_goal=config.research_goal, provider="harness", model=harness,
            population_size=1, max_generations=None, model_call_budget=None,
            resumed=False, generation=0, workspace=str(ws_dir))
    except BaseException:
        # No half-made run: the same --run-id must work on retry.
        for f in written:
            f.unlink(missing_ok=True)
        shutil.rmtree(run_dir, ignore_errors=True)
        raise
    return Workspace(dir=ws_dir, run_dir=run_dir, pack=pack.name, problem=pack.checker)


def program_text(pack: Any, goal: str | None, max_checks: int | None = None) -> str:
    problem = get_problem(pack.checker)
    root = "yes, vertex 0" if problem.needs_root else "no"
    parts = [
        f"# evoalgo: {pack.title}",
        "",
        "You are searching for a correct, efficient dynamic graph algorithm.",
        f"You edit one file, `{CANDIDATE_FILE}`, and grade it with `evoalgo check`.",
        "",
        "## Problem",
        "",
        f"- Graph: {'directed' if problem.directed else 'undirected'}; root: {root}.",
        "- Implement `init(graph)`, `insert_edge(graph, edge, state)`, "
        "`delete_edge(graph, edge, state)`; each returns the new state.",
        "- `graph` is the 0/1 adjacency matrix (list of lists) after the update; "
        "`edge` is `(u, v)`. One update flips one entry.",
        "- No globals, no module-level mutable state, standard library only.",
        "",
        "State contract (what the grader reads):",
        "",
        "```text",
        problem.STATE_CONTRACT,
        "```",
    ]
    if goal:
        parts += ["", "## Goal for this run", "", goal]
    parts += [
        "",
        "## Loop",
        "",
        "1. Edit `candidate.py`.",
        "2. Run `evoalgo check` (default level `search`: all non-isomorphic graphs",
        "   up to n = 4, seconds). Use `--level examples` for a faster n <= 3 check.",
        "3. Read the JSON verdict. On FAIL, `first_failure` names the graph, the",
        "   operation and what was wrong; fix the cause, not the symptom.",
        "4. Keep a change if it fixes a failure or lowers `work_ratio` without",
        "   breaking correctness; otherwise revert it.",
        "5. Every check is logged to `results.tsv` and the run folder; do not edit them.",
        "6. When the search grade passes and you cannot lower `work_ratio` further,",
        "   run `evoalgo check --final` once (n <= 5, up to ~12 minutes; give the",
        "   shell command a timeout of at least 15 minutes) and report.",
        *([f"7. This run allows {max_checks} checks before the final grade (every level",
           "   counts) and one final grade; `evoalgo check` refuses more."] if max_checks else []),
        "",
        "Correct first, then cheaper. Prefer the simpler of two equally good versions.",
        "A recompute-from-scratch solution is correct but no cheaper than recomputing.",
        "Its `work_ratio` is not 1 (the baseline is a separate offline implementation),",
        "so judge progress against your own recompute version: the research question",
        "is how far below it you can go.",
        "",
        "## Research brief",
        "",
        pack.brief.strip(),
        "",
    ]
    return "\n".join(parts)


def _verifier(problem_name: str, config: RunConfig, level: str, update_mode: str) -> Verifier:
    problem = get_problem(problem_name)
    if level == "examples":
        from .agents.examples import PUBLIC_N_MAX, PUBLIC_TIMEOUT_SECONDS
        return Verifier(problem=problem,
                        sandbox=Sandbox(timeout_seconds=PUBLIC_TIMEOUT_SECONDS, directed=problem.directed),
                        bound_n_max=PUBLIC_N_MAX, bound_n_random=0, bound_seq_len_max=1,
                        bound_seq_count=0, bound_seed=0, relabels_per_class=0, use_offline=False,
                        update_mode=update_mode)
    b = config.bound
    if level == "search":
        return Verifier(problem=problem,
                        sandbox=Sandbox(timeout_seconds=config.timeout_seconds, directed=problem.directed),
                        bound_n_max=min(config.search_n_max, b.n_max), bound_n_random=0,
                        bound_seq_len_max=b.seq_len_max, bound_seq_count=config.search_seq_count,
                        bound_seed=b.seed, relabels_per_class=1, update_mode=update_mode)
    return Verifier(problem=problem,
                    sandbox=Sandbox(timeout_seconds=config.final_timeout_seconds, directed=problem.directed),
                    bound_n_max=b.n_max, bound_n_random=b.n_random, bound_seq_len_max=b.seq_len_max,
                    bound_seq_count=b.seq_count, bound_seed=b.seed, update_mode=update_mode)


def check(ws: Workspace, file: Path | str | None = None, level: str = "search",
          note: str = "", final: bool = False) -> dict[str, Any]:
    """Grade a candidate file, record it in the run, return the report.

    Only the workspace's own candidate.py is graded (a regular file, not a
    symlink), so every recorded grade belongs to the file the session edits.
    """
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}")
    src = ws.dir / CANDIDATE_FILE
    if file and not (Path(file).exists() and src.exists() and os.path.samefile(file, src)):
        raise ValueError(f"only the workspace's {CANDIDATE_FILE} is graded; edit it and run "
                         f"`evoalgo check` without a file argument")
    if src.is_symlink() or not src.is_file():
        raise FileNotFoundError(f"{src} must be a regular file (not a symlink)")
    with _locked(ws.run_dir):
        events_now = read_events(ws.run_dir)
        if any(e.get("type") == "run_end" for e in events_now):
            raise RuntimeError("this workspace is finished; start a new one with `evoalgo init`")
        return _check_locked(ws, src, level, note, final, events_now)


@contextmanager
def _locked(run_dir: Path):
    """One check or finish at a time per run (agents run shell commands in parallel)."""
    with open(run_dir / ".lock", "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _best(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Best PASS so far: highest grade level, then lowest work ratio."""
    rank = {lvl: i for i, lvl in enumerate(LEVELS)}
    passing = [e for e in events if e.get("type") == "candidate_verified" and e.get("state") == "PASS"]
    return min(passing, key=lambda e: (-rank.get(e.get("level"), 0),
                                       e.get("work_ratio") if e.get("work_ratio") is not None
                                       else float("inf")), default=None)


def _check_locked(ws: Workspace, src: Path, level: str, note: str, final: bool,
                  events_now: list[dict[str, Any]]) -> dict[str, Any]:
    config = RunConfig.load(ws.run_dir / "config.yaml")
    pack = resolve_pack(ws.pack)
    n = 1 + max((e.get("gen", 0) for e in events_now if e.get("type") == "gen_start"), default=0)
    if n > 999:
        raise RuntimeError("this workspace has 999 checks; start a new one with `evoalgo init`")
    if config.max_checks is not None:
        done = _with_roles(events_now)
        if final and any(e.get("role") == "final" for e in done):
            # Each final grade reports its first failure: more than one would
            # be extra search outside the budget.
            raise RuntimeError("the final grade has run; run `evoalgo finish`")
        if not final and sum(e.get("role") != "final" for e in done) >= config.max_checks:
            raise RuntimeError(f"check budget used up ({config.max_checks} checks); "
                               "run `evoalgo check --final`, then `evoalgo finish`")
    cid = f"gen{n:03d}_c01"
    snapshot = ws.run_dir / "candidates" / f"{cid}.py"
    code = src.read_bytes()
    snapshot.write_bytes(code)
    # Recorded with the grade so a report can tell whether the graded file
    # was changed afterwards.
    sha256 = hashlib.sha256(code).hexdigest()

    events = EventLog(ws.run_dir)
    prev = _last_kept(events_now)
    parents = [prev] if prev else []
    events.emit("gen_start", gen=n)
    events.emit("candidate_generated", id=cid, gen=n, parent_ids=parents,
                role="final" if final else "harness", level=level, note=note[:500] or None,
                sha256=sha256)
    started = time.monotonic()
    verifier = _verifier(ws.problem, config, level, pack.update_mode)
    try:
        result = verifier.verify(Candidate(id=cid, code_path=str(snapshot), generation=n))
    except BaseException as e:
        # Close the generation so the log and the UI never show a dangling check.
        reason = "interrupted" if isinstance(e, KeyboardInterrupt) else f"{type(e).__name__}: {e}"
        events.emit("candidate_verified", id=cid, gen=n, state="CRASH", fitness=0.0,
                    work_ratio=None, timeout=False, tests_passed=0, tests_total=0,
                    failing_case=None, error=f"check aborted: {reason}"[:500], level=level)
        _commit(events, n, cid, parents, "CRASH", 0.0, None, level, read_events(ws.run_dir))
        raise
    seconds = round(time.monotonic() - started, 1)
    verdict = result.state.value
    events.emit("candidate_verified", id=cid, gen=n, state=verdict, fitness=result.fitness,
                work_ratio=result.work_ratio, timeout=result.timeout,
                tests_passed=result.tests_passed, tests_total=result.tests_total,
                failing_case=result.failing_case, error=result.error_message, level=level)
    _commit(events, n, cid, parents, verdict, result.fitness, result.work_ratio, level,
            read_events(ws.run_dir))
    if final:
        events.emit("final_graded", id=cid, state=verdict, fitness=result.fitness,
                    work_ratio=result.work_ratio, tests_passed=result.tests_passed,
                    tests_total=result.tests_total, timeout=result.timeout,
                    failing_case=result.failing_case, n_max=verifier.n_max, duration_s=seconds,
                    sha256=sha256)

    wr = "" if result.work_ratio is None else f"{result.work_ratio:.4f}"
    clean_note = " ".join(note.split())[:200]
    results = ws.dir / RESULTS_FILE
    if not results.exists():
        results.write_text(RESULTS_HEADER)
    with open(results, "a") as f:
        f.write(f"{n}\t{cid}\t{level}\t{verdict}\t{result.tests_passed}\t{result.tests_total}"
                f"\t{wr}\t{seconds}\t{clean_note}\n")

    report: dict[str, Any] = {
        "check": n, "candidate_id": cid, "level": level, "verdict": verdict,
        "passed": result.tests_passed, "total": result.tests_total,
        "work_ratio": result.work_ratio, "seconds": seconds,
        "scope": _scope(level, verifier.n_max),
    }
    if result.failing_case:
        report["first_failure"] = result.failing_case
    if result.error_message:
        report["error"] = result.error_message[:2000]
    if result.timeout:
        report["timeout"] = True
    return report


def _commit(events: EventLog, n: int, cid: str, parents: list[str], state: str,
            fitness: float, work_ratio: float | None, level: str,
            all_events: list[dict[str, Any]]) -> None:
    """gen_committed with this check as the population and the best PASS so far as best."""
    best = _best(all_events)
    events.emit("gen_committed", gen=n,
                population=[{"id": cid, "parent_ids": parents, "state": state,
                             "fitness": fitness, "work_ratio": work_ratio}],
                best_id=best["id"] if best else None,
                best_fitness=best["fitness"] if best else fitness,
                best_work_ratio=best.get("work_ratio") if best else None,
                model_calls=None, level=level)


def _with_roles(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """candidate_verified events tagged with their candidate's role."""
    roles = {e.get("id"): e.get("role") for e in events if e.get("type") == "candidate_generated"}
    return [{**e, "role": roles.get(e.get("id"))} for e in events
            if e.get("type") == "candidate_verified"]


def snapshot_intact(run_dir: Path, graded: dict[str, Any]) -> bool | None:
    """Whether a graded snapshot still has the bytes it was graded with;
    None for grades recorded before hashes existed."""
    if not graded.get("sha256"):
        return None
    path = Path(run_dir) / "candidates" / f"{graded['id']}.py"
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == graded["sha256"]


def _scope(level: str, n_max: int) -> str:
    if level == "examples":
        return f"all non-isomorphic graphs n <= {n_max}, every single-edge flip"
    return f"all non-isomorphic graphs n <= {n_max}, every single flip, plus update sequences"


def _last_kept(events: list[dict[str, Any]]) -> str | None:
    """The most recent passing check, as the lineage parent of the next one."""
    for e in reversed(events):
        if e.get("type") == "candidate_verified" and e.get("state") == "PASS":
            return e["id"]
    return None


def finish(ws: Workspace, reason: str = "harness_done") -> dict[str, Any]:
    """Close the run: best = best PASS of the highest level reached, by work ratio."""
    with _locked(ws.run_dir):
        events = read_events(ws.run_dir)
        if any(e.get("type") == "run_end" for e in events):
            raise RuntimeError("this workspace is already finished")
        verified = [e for e in events if e.get("type") == "candidate_verified"]
        best = _best(events)
        final = next((e for e in reversed(events) if e.get("type") == "final_graded"), None)
        return EventLog(ws.run_dir).emit(
            "run_end", stop_reason=reason, generation=len(verified),
            best_candidate_id=best["id"] if best else None,
            best_fitness=best["fitness"] if best else max((e.get("fitness") or 0 for e in verified),
                                                          default=0.0),
            best_work_ratio=best.get("work_ratio") if best else None,
            model_calls=None, final_grade=final)


SKILL_NAME = "evoalgo"


def skill_source() -> Path:
    return Path(__file__).parent / "skill" / SKILL_NAME


def skill_targets(scope: str, project: Path | None = None) -> list[Path]:
    """Folders the three harnesses read (verified for Claude Code 2.1.303,
    Codex 0.163.0, opencode/enlcode): `.agents/skills` (Codex, opencode)
    and `.claude/skills` (Claude Code, opencode)."""
    base = (project or Path.cwd()).resolve() if scope == "project" else Path.home()
    return [base / ".agents" / "skills", base / ".claude" / "skills"]


def install_skill(scope: str = "user", project: Path | None = None,
                  force: bool = False) -> list[Path]:
    src = skill_source()
    written = []
    for root in skill_targets(scope, project):
        dest = root / SKILL_NAME
        if dest.exists() or dest.is_symlink():
            if not force:
                raise FileExistsError(f"{dest} exists; use --force to replace it")
            if dest.is_symlink() or dest.is_file():
                dest.unlink()
            else:
                shutil.rmtree(dest)
        root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns("__pycache__"))
        written.append(dest)
    return written
