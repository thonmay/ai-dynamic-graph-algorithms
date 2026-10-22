"""Evaluation campaign: run a grid of (mode, problem, seed) and collect results.

    python scripts/campaign.py run  campaign/plan.yaml [--parallel 4] [--dry-run]
    python scripts/campaign.py report campaign/plan.yaml

`run` is resumable. A cell whose run folder already ended (run_end event) is
skipped. An unfinished orchestrator cell is resumed. An unfinished harness
cell (a coding-agent session cannot be resumed) is closed as aborted, kept as
evidence under a new name, and restarted, at most `harness.max_attempts`
times in total. Every attempt is reported.

`report` reads only the run folders and the saved harness streams, so it can
be re-run at any time. Metrics shared by all modes: LLM turns and tokens.
Orchestrator runs also report role calls (each is a multi-turn tool loop).

Modes:
  orchestrator   evoalgo's multi-agent loop (generate, reflect, repair)
  no_reflection  same with the reflection role off; repair is then never
                 used either, since repair works from reflections
  harness        one coding agent (enlcode) uses the evoalgo skill
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from statistics import median

import yaml

REPO = Path(__file__).resolve().parents[1]
EVOALGO = REPO / ".venv" / "bin" / "evoalgo"
sys.path.insert(0, str(REPO / "src"))

from evoalgo.agents.harness import harness_env  # noqa: E402
from evoalgo.events import read_events  # noqa: E402
from evoalgo.workspace import snapshot_intact  # noqa: E402

HARNESS_PROMPT = (
    "Use the evoalgo skill: find a correct dynamic algorithm for pack {pack}. "
    "Create the workspace with run id {run_id}, --harness enlcode, --max-checks {max_checks} "
    "and --goal \"{goal}\". "
    "Do at most {max_checks} checks, then run the final check and finish."
)
ORCHESTRATOR_MODES = ("orchestrator", "no_reflection", "dynamic_agents")


def load_plan(path: str) -> dict:
    plan = yaml.safe_load(Path(path).read_text())
    plan["out"] = REPO / plan["out"]  # independent of the caller's cwd
    return plan


def cells(plan: dict) -> list[dict]:
    """Seed-major order: after each seed round every (mode, problem) has one
    run, so a campaign stopped early still compares all modes."""
    return [{"mode": mode, "pack": pack, "seed": seed,
             "run_id": f"{plan['name']}_{mode}_{pack}_s{seed}"}
            for seed in plan["seeds"] for pack in plan["problems"] for mode in plan["modes"]]


def run_dir(cell: dict) -> Path:
    return REPO / "runs" / cell["run_id"]


def is_done(path: Path) -> bool:
    return any(e.get("type") == "run_end" for e in read_events(path))


def aborted_attempts(cell: dict) -> list[Path]:
    return sorted(run_dir(cell).parent.glob(cell["run_id"] + "_aborted_*"))


RETRY_REASONS = ("aborted", "agent_stopped")  # infrastructure, not the agent's result


def _retry_harness(plan: dict, cell: dict, path: Path) -> bool:
    """An ended harness attempt that the agent did not finish is retried
    (up to max_attempts); a timeout or a finished session is final."""
    if cell["mode"] != "harness":
        return False
    events = read_events(path)
    end = next((e for e in reversed(events) if e.get("type") == "run_end"), {})
    # An attempt that already found a passing candidate is kept: retrying
    # would move it aside and report the cell from the new attempt only.
    passed = any(e.get("type") in ("candidate_verified", "final_graded") and e.get("state") == "PASS"
                 for e in events)
    tries = len(aborted_attempts(cell)) + 1
    return (end.get("stop_reason") in RETRY_REASONS and not passed
            and tries < plan["harness"]["max_attempts"])


def orchestrator_config(plan: dict, cell: dict) -> Path:
    base = dict(plan["orchestrator"])
    base.update(pack=cell["pack"], problem=cell["pack"], research_goal=plan["goal"],
                selection_seed=cell["seed"], workdir="runs",
                reflection=cell["mode"] != "no_reflection",
                dynamic_agents=cell["mode"] == "dynamic_agents")
    if cell["mode"] == "dynamic_agents":
        base.update(plan.get("dynamic_agents") or {})
    path = plan["out"] / "configs" / f"{cell['run_id']}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(base, sort_keys=True))
    return path


def end_harness_run(path: Path, reason: str, move: bool) -> Path:
    """End an unfinished harness run with ``reason`` and optionally move it aside.

    Holds the run's check lock (the one `evoalgo check` takes), so a check an
    old agent session left running finishes first, and a later one fails on
    the moved folder. Writes run_end directly; `evoalgo finish` would wait on
    the lock held here.
    """
    with open(path / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not is_done(path):
            from evoalgo.events import EventLog
            verified = [e for e in read_events(path) if e.get("type") == "candidate_verified"]
            EventLog(path).emit("run_end", stop_reason=reason, generation=len(verified),
                                best_candidate_id=None, best_fitness=None, best_work_ratio=None,
                                model_calls=None, final_grade=None)
        if not move:
            return path
        dest = path.with_name(f"{path.name}_aborted_{int(time.time())}")
        path.rename(dest)
    return dest


def _run(cmd: list[str], out: Path, timeout: int, env: dict) -> str:
    """Run in a new process group; on timeout stop the whole group."""
    with open(out, "ab") as f:
        f.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} {' '.join(cmd[:4])}\n".encode())
        f.flush()
        proc = subprocess.Popen(cmd, cwd=REPO, env=env, stdout=f, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, start_new_session=True)
        try:
            return str(proc.wait(timeout=timeout))
        except subprocess.TimeoutExpired:
            for sig, grace in ((signal.SIGTERM, 30), (signal.SIGKILL, 10)):
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    proc.wait(timeout=grace)
                    break
                except subprocess.TimeoutExpired:
                    continue
            return "timeout"


def run_cell(plan: dict, cell: dict, dry: bool) -> dict:
    path = run_dir(cell)
    if path.exists() and is_done(path) and not _retry_harness(plan, cell, path):
        return {**cell, "status": "skipped (done)"}
    # Temp files of every child (sandbox runner scripts, example checks) go to
    # the project scratch area, not /tmp.
    scratch = Path(plan.get("scratch", "/proj/MPS/MPS_DEV_REPO/ethomdt/evoalgo-scratch")) / cell["run_id"]
    scratch.mkdir(parents=True, exist_ok=True)
    # Allow-listed environment (no unrelated keys/passwords for the agent);
    # the orchestrator modes also need the key variable of their endpoint.
    env = harness_env("enlcode", PATH=f"{REPO / '.venv' / 'bin'}:{os.environ.get('PATH', '')}",
                      TMPDIR=str(scratch))
    key_vars = {"ERICAI_ACCESS_TOKEN", "OPENROUTER_API_KEY", "OPENAI_API_KEY",
                (plan.get("orchestrator") or {}).get("api_key_env")}
    for name in key_vars:
        if cell["mode"] in ORCHESTRATOR_MODES and name and name in os.environ:
            env[name] = os.environ[name]
    logs = plan["out"] / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    if cell["mode"] in ORCHESTRATOR_MODES:
        cmd = ([str(EVOALGO), "resume", str(path)] if path.exists() else
               [str(EVOALGO), "start", str(orchestrator_config(plan, cell)), "--run-id", cell["run_id"]])
        out, timeout = logs / f"{cell['run_id']}.log", plan["timeouts"]["orchestrator_seconds"]
    else:
        tries = len(aborted_attempts(cell)) + (1 if path.exists() else 0)
        if tries >= plan["harness"]["max_attempts"]:
            if path.exists() and not dry and not is_done(path):
                end_harness_run(path, "gave_up", move=False)
            return {**cell, "status": f"gave up after {tries} attempts"}
        if path.exists() and not dry:
            end_harness_run(path, "aborted", move=True)  # keeps an existing run_end
        prompt = HARNESS_PROMPT.format(pack=cell["pack"], goal=plan["goal"], run_id=cell["run_id"],
                                       max_checks=plan["harness"]["max_checks"])
        cmd = [plan["harness"]["bin"], "run", "-m", plan["harness"]["model"],
               "--agent", plan["harness"]["agent"], "--format", "json", prompt]
        # One stream per attempt, so tokens of aborted attempts stay separate.
        out = plan["out"] / "harness" / f"{cell['run_id']}.attempt{tries + 1}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        timeout = plan["timeouts"]["harness_seconds"]
    if dry:
        return {**cell, "status": "would run", "cmd": " ".join(cmd[:4])}
    started = time.time()
    code = _run(cmd, out, timeout, env)
    if cell["mode"] == "harness" and code == "timeout" and path.exists() and not is_done(path):
        # The cell ends as a timeout (counts as no PASS) instead of being retried.
        end_harness_run(path, "timeout", move=False)
    if cell["mode"] == "harness" and code != "timeout" and path.exists() and not is_done(path):
        # The agent stopped without `evoalgo finish` (e.g. an empty final
        # turn). End the attempt here; the next `run` retries the cell.
        end_harness_run(path, "agent_stopped", move=False)
    status = "done" if path.exists() and is_done(path) else f"incomplete (exit {code})"
    shutil.rmtree(scratch, ignore_errors=True)
    return {**cell, "status": status, "minutes": round((time.time() - started) / 60, 1)}


def cmd_run(args) -> int:
    plan = load_plan(args.plan)
    todo = cells(plan)
    print(f"{len(todo)} cells, parallel {args.parallel}", flush=True)
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        for result in pool.map(lambda c: run_cell(plan, c, args.dry_run), todo):
            print(json.dumps(result), flush=True)
    return 0


# -- report ------------------------------------------------------------------

def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _active_minutes(events: list[dict], until: str | None = None) -> float | None:
    """Wall time summed per session (a resume starts a new one), so time a
    run spent dead between sessions is not counted."""
    sessions, cur = [], []
    for e in events:
        if until and e.get("ts") and e["ts"] > until:
            break
        if e.get("type") == "run_start" and cur:
            sessions.append(cur)
            cur = []
        if e.get("ts"):
            cur.append(e["ts"])
    if cur:
        sessions.append(cur)
    total = sum((_ts(s[-1]) - _ts(s[0])).total_seconds() for s in sessions if len(s) > 1)
    return round(total / 60, 1) if sessions else None


def _harness_usage(streams: list[Path]) -> dict:
    """Token use from enlcode's event stream, counted like OpenAI usage:
    prompt = input + cache reads + cache writes, completion = output + reasoning."""
    u = {"turns": 0, "prompt_tokens": 0, "completion_tokens": 0}
    for stream in streams:
        for line in stream.read_text(errors="replace").splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not (isinstance(e, dict) and e.get("type") == "step_finish"):
                continue
            t = (e.get("part") or {}).get("tokens") or {}
            cache = t.get("cache") or {}
            u["turns"] += 1
            u["prompt_tokens"] += int(t.get("input") or 0) + int(cache.get("read") or 0) + int(cache.get("write") or 0)
            u["completion_tokens"] += int(t.get("output") or 0) + int(t.get("reasoning") or 0)
    return u


def _orchestrator_usage(path: Path) -> dict:
    u = {"turns": 0, "prompt_tokens": 0, "completion_tokens": 0}
    for p in (path / "prompt_logs").glob("call_*.json"):
        try:
            entry = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        usage = entry.get("usage") or {}
        u["turns"] += entry.get("steps") or 0
        u["prompt_tokens"] += usage.get("prompt_tokens") or 0
        u["completion_tokens"] += usage.get("completion_tokens") or 0
    return u


def _specialist_gains(ev: list[dict]) -> int:
    made = {e["id"] for e in ev if e.get("type") == "candidate_generated" and e.get("role") == "specialist"}
    gains, prev = 0, None
    for e in ev:
        if e.get("type") == "gen_committed":
            best = e.get("best_id")
            gains += best != prev and best in made
            prev = best
    return gains


def summarize_run(plan: dict, cell: dict) -> dict:
    path = run_dir(cell)
    row = {**cell, "attempts": len(aborted_attempts(cell)) + (1 if path.exists() else 0),
           "exists": path.exists()}
    if not path.exists():
        return row
    ev = read_events(path)
    end = next((e for e in reversed(ev) if e.get("type") == "run_end"), None)
    harness = cell["mode"] == "harness"
    # The outcome: the orchestrator's chosen final grade, or the agent's last --final.
    finals = [e for e in ev if e.get("type") == "final_graded"]
    final = ((end or {}).get("final_grade") if not harness else None) or (finals[-1] if finals else None)
    # A PASS on the n <= 3 examples level is weaker than the search grade; skip it.
    verified = [e for e in ev if e.get("type") == "candidate_verified" and e.get("level") != "examples"]
    first_pass = next((e for e in verified if e.get("state") == "PASS"), None)
    streams = sorted((plan["out"] / "harness").glob(f"{cell['run_id']}.attempt*.jsonl"))
    usage = _harness_usage(streams[-1:]) if harness else _orchestrator_usage(path)
    all_usage = _harness_usage(streams) if harness else usage
    row.update(
        ended=bool(end), stop_reason=(end or {}).get("stop_reason"),
        final_state=(final or {}).get("state"), final_pass=(final or {}).get("state") == "PASS",
        final_id=(final or {}).get("id"), final_work_ratio=(final or {}).get("work_ratio"),
        # The graded file still has the bytes it was graded with (None: no
        # hash recorded, runs from before hashing).
        final_intact=snapshot_intact(path, final) if final else None,
        final_tests=(final or {}).get("tests_total"), final_runs=len(finals),
        graded_candidates=len(verified), search_pass=bool(first_pass),
        first_pass_gen=(first_pass or {}).get("gen"),
        first_pass_minutes=_active_minutes(ev, first_pass["ts"]) if first_pass else None,
        role_calls=None if harness else len([e for e in ev if e.get("type") == "agent_call_end"]),
        llm_turns=usage["turns"], prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        all_attempts_tokens=all_usage["prompt_tokens"] + all_usage["completion_tokens"],
        active_minutes=_active_minutes(ev),
        # Dynamic agent generation: plateaus, specialists, and whether a
        # specialist's candidate ever became the population best.
        plateaus=sum(e.get("type") == "plateau_detected" for e in ev),
        specialists_spawned=sum(e.get("type") == "agent_spawned" for e in ev),
        specialist_candidates=len({e.get("id") for e in ev if e.get("type") == "candidate_generated"
                                   and e.get("role") == "specialist"}),
        # Generations in which a specialist's candidate became the new
        # population best (counted from the log, so a specialist still active
        # at the end of the run counts too).
        specialist_gains=_specialist_gains(ev),
        final_by_specialist=bool(final) and any(
            e.get("type") == "candidate_generated" and e.get("role") == "specialist"
            and e.get("id") == (final or {}).get("id") for e in ev),
    )
    return row


def cmd_reference(args) -> int:
    """Grade the recompute-from-scratch candidate of each problem with the
    final grade, so work ratios can be read against plain recomputation
    (the offline baseline runs on a numpy array and is slower than the same
    algorithm on lists, so recompute scores well below 1)."""
    from evoalgo.candidate import Candidate
    from evoalgo.cli import _generate_known_good_candidate
    from evoalgo.config import RunConfig
    from evoalgo.workspace import _verifier
    from evoalgo.packs import resolve_pack
    plan = load_plan(args.plan)
    ref_path = plan["out"] / "reference.json"
    refs = json.loads(ref_path.read_text()) if ref_path.is_file() else {}
    scratch = Path(plan.get("scratch", "/proj/MPS/MPS_DEV_REPO/ethomdt/evoalgo-scratch")) / "reference"
    scratch.mkdir(parents=True, exist_ok=True)
    for pack in plan["problems"]:
        if pack in refs:
            continue
        cfg = RunConfig(pack=pack, problem=pack, **{k: v for k, v in plan["orchestrator"].items()
                                                   if k in ("final_timeout_seconds", "bound")})
        f = scratch / f"{pack}_recompute.py"
        f.write_text(_generate_known_good_candidate(pack))
        started = time.time()
        r = _verifier(pack, cfg, "full", resolve_pack(pack).update_mode).verify(
            Candidate(id="recompute", code_path=str(f), generation=0))
        refs[pack] = {"state": r.state.value, "work_ratio": r.work_ratio, "tests_total": r.tests_total,
                      "minutes": round((time.time() - started) / 60, 1)}
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.write_text(json.dumps(refs, indent=2) + "\n")
        print(pack, refs[pack], flush=True)
    shutil.rmtree(scratch, ignore_errors=True)
    return 0


def cmd_report(args) -> int:
    plan = load_plan(args.plan)
    rows = [summarize_run(plan, c) for c in cells(plan)]
    ref_path = plan["out"] / "reference.json"
    refs = json.loads(ref_path.read_text()) if ref_path.is_file() else {}
    for r in rows:
        ref = (refs.get(r["pack"]) or {}).get("work_ratio")
        wr = r.get("final_work_ratio")
        # < 1: cheaper than recomputing from scratch on the same graphs.
        r["work_vs_recompute"] = round(wr / ref, 3) if wr is not None and ref else None
    out = plan["out"]
    out.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with open(out / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    def med(xs):
        xs = [x for x in xs if x is not None]
        return round(median(xs), 3) if xs else "-"

    lines = [f"# Campaign {plan['name']}", "",
             "Medians over ended runs. Work ratios over final-grade PASS runs only;",
             "'vs recompute' divides by the recompute-from-scratch candidate's ratio",
             "(reference.json), so 1.0 = no better than recomputing.", "",
             "| mode | problem | ended | final PASS | work ratio | vs recompute | min to first PASS | LLM turns | tokens (k) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for pack in plan["problems"]:
        for mode in plan["modes"]:
            rs = [r for r in rows if r["mode"] == mode and r["pack"] == pack and r.get("ended")]
            ok = [r for r in rs if r.get("final_pass")]
            lines.append(
                f"| {mode} | {pack} | {len(rs)}/{len(plan['seeds'])} | {len(ok)}/{len(rs)} | "
                f"{med([r['final_work_ratio'] for r in ok])} | {med([r['work_vs_recompute'] for r in ok])} | "
                f"{med([r['first_pass_minutes'] for r in rs])} | {med([r['llm_turns'] for r in rs])} | "
                f"{med([(r['prompt_tokens'] + r['completion_tokens']) / 1000 for r in rs])} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("plan")
    r.add_argument("--parallel", type=int, default=4)
    r.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("report")
    p.add_argument("plan")
    f = sub.add_parser("reference", help="grade recompute-from-scratch per problem (once)")
    f.add_argument("plan")
    args = ap.parse_args()
    return {"run": cmd_run, "report": cmd_report, "reference": cmd_reference}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
