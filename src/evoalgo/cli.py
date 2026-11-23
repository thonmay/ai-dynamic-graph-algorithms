# AI-assisted code: generated and revised with Qwen3.8-Flash-Next, GLM-5.2, Claude Opus 5.5, DeepSeek-V4-Flash and Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""CLI: argument parsing and command dispatch.

Commands:
  evoalgo run configure   - set and validate run parameters
  evoalgo run start       - begin the evolutionary loop
  evoalgo run status      - show current generation, best fitness
  evoalgo run resume      - reload last committed generation and continue
  evoalgo run export      - save results as report
  evoalgo run history     - list previous runs with summaries
  evoalgo verify          - run verifier self-test (FR-VER-08)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

from .config import ConfigError, RunConfig, Bound, VALID_PROBLEMS
from .orchestrator import Orchestrator


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evoalgo",
        description="Evolutionary code-repair system for dynamic graph algorithm discovery",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run configure
    p_configure = subparsers.add_parser("configure", help="set and validate run parameters")
    p_configure.add_argument("--problem", choices=sorted(VALID_PROBLEMS), default="dynamic_mcs")
    p_configure.add_argument("--model", default=None, help="model id (null = provider default)")
    p_configure.add_argument("--population", type=int, default=8, help="population size 1-50")
    p_configure.add_argument("--generations", type=int, default=50, help="max generations 1-1000")
    p_configure.add_argument("--timeout", type=int, default=30, help="per-candidate timeout seconds")
    p_configure.add_argument("--n-max", type=int, default=5, help="max graph size for testing")
    p_configure.add_argument("--seq-len", type=int, default=20, help="max operations per sequence")
    p_configure.add_argument("--seq-count", type=int, default=10, help="sequences per base graph")
    p_configure.add_argument("--seed", type=int, default=1337, help="random seed")
    p_configure.add_argument("--elitism-k", type=int, default=2, help="top-k survivors")
    p_configure.add_argument("--workdir", default="runs", help="run directory root")
    p_configure.add_argument("--no-early-stop", action="store_true",
                             help="keep evolving past fitness 1.0 instead of stopping on first success")
    p_configure.add_argument("--output", "-o", default="config.yaml", help="output config file")

    # run start
    p_start = subparsers.add_parser("start", help="begin the evolutionary loop")
    p_start.add_argument("config", help="path to config.yaml")
    p_start.add_argument("--run-id", default=None, help="run identifier (auto-generated if omitted)")
    p_start.add_argument("--model", default=None, help="override model id (e.g. openrouter/qwen/qwen3-coder)")

    # run status
    p_status = subparsers.add_parser("status", help="show current run status")
    p_status.add_argument("run_dir", help="path to run directory")
    p_status.add_argument("--json", action="store_true", help="machine-readable summary")

    # run resume
    p_resume = subparsers.add_parser("resume", help="resume from last checkpoint")
    p_resume.add_argument("run_dir", help="path to run directory")

    # run export
    p_export = subparsers.add_parser("export", help="export run results")
    p_export.add_argument("run_dir", help="path to run directory")

    # run history
    p_history = subparsers.add_parser("history", help="list previous runs")
    p_history.add_argument("--workdir", default="runs", help="run directory root")
    p_history.add_argument("--json", action="store_true", help="machine-readable list")

    # control (steer a running run between generations)
    p_control = subparsers.add_parser("control", help="pause/resume/stop or steer a running run")
    p_control.add_argument("run_dir", help="path to run directory")
    p_control.add_argument("cmd", choices=["pause", "resume", "stop", "hint", "set"])
    p_control.add_argument("args", nargs="*",
                           help="hint: TEXT ('' clears it); set: FIELD VALUE "
                                "(model_call_budget, population_size)")

    # ui (web server)
    p_ui = subparsers.add_parser("ui", help="serve the web UI (launch, monitor, steer, replay)")
    p_ui.add_argument("--runs", default="runs", help="run directory root")
    p_ui.add_argument("--host", default="127.0.0.1",
                      help="bind address (default loopback; access needs the printed token link)")
    p_ui.add_argument("--port", type=int, default=8765)

    # events (event log maintenance)
    p_events = subparsers.add_parser("events", help="event log tools")
    p_events.add_argument("action", choices=["backfill"],
                          help="backfill: build events.jsonl from generation checkpoints")
    p_events.add_argument("run_dirs", nargs="+", help="run directories")
    p_events.add_argument("--force", action="store_true", help="rebuild an existing events.jsonl")

    # verify (self-test)
    p_verify = subparsers.add_parser("verify", help="run verifier self-test (FR-VER-08)")
    p_verify.add_argument("--problem", choices=sorted(VALID_PROBLEMS), default="dynamic_bfs")
    p_verify.add_argument("--n-max", type=int, default=None,
                          help="max graph size for self-test (default 5)")
    p_verify.add_argument("--relabels", type=int, default=0,
                          help="deterministic relabels per nauty class (default 0; "
                               "use 2 for the full documented universe; undirected "
                               "problems always use every labelled graph)")
    p_verify.add_argument("--chunk-size", type=int, default=None,
                          help="base graphs per sandbox subprocess (default: auto "
                               "-- 2000 serial, 1000 when parallelizing)")
    p_verify.add_argument("--workers", type=int, default=None,
                          help="parallel chunk workers (default: min(8, cpu); "
                               "1 = serial, reproduces the original path)")
    p_verify.add_argument("--timeout", type=int, default=120,
                          help="per-chunk wall-clock seconds (default 120)")

    # harness workspaces (a coding agent drives the loop, evoalgo grades)
    p_init = subparsers.add_parser(
        "init", help="create a workspace for a coding agent (program.md, candidate.py)")
    p_init.add_argument("pack", help="problem pack name, e.g. dynamic_bfs")
    p_init.add_argument("dir", nargs="?", default=None,
                        help="where the agent works (default: the run folder itself)")
    p_init.add_argument("--runs", default="runs", help="run directory root (for the UI)")
    p_init.add_argument("--run-id", default=None)
    p_init.add_argument("--goal", default=None, help="research goal for this run")
    p_init.add_argument("--harness", default=None,
                        help="which agent drives it (claude, codex, opencode), shown in the UI")
    p_init.add_argument("--max-checks", type=int, default=None,
                        help="graded checks allowed before the final grade (default: no limit)")

    p_check = subparsers.add_parser("check", help="grade a candidate in a workspace, print JSON")
    p_check.add_argument("file", nargs="?", default=None,
                         help="the workspace's candidate.py (the only file graded; default)")
    p_check.add_argument("--level", choices=["examples", "search", "full"], default="search",
                         help="examples: n<=3, s; search: n<=4, s (default); full: n<=5, minutes")
    p_check.add_argument("--final", action="store_true",
                         help="the independent final grade (implies --level full)")
    p_check.add_argument("--note", default="", help="what changed, logged in results.tsv")
    p_check.add_argument("--workspace", default=".", help="workspace directory (default: cwd)")

    p_finish = subparsers.add_parser("finish", help="close a workspace run")
    p_finish.add_argument("--workspace", default=".")
    p_finish.add_argument("--reason", default="harness_done")

    subparsers.add_parser("packs", help="list problem packs as JSON")

    p_skill = subparsers.add_parser("skill", help="install the evoalgo agent skill")
    p_skill.add_argument("--install", action="store_true", required=True)
    p_skill.add_argument("--project", default=None,
                         help="install into this repo (.agents/skills, .claude/skills) "
                              "instead of the home directory")
    p_skill.add_argument("--force", action="store_true", help="replace an existing copy")

    # formalize (Lean proof of a PASS candidate)
    p_formalize = subparsers.add_parser(
        "formalize",
        help="dispatch lean-prover agent to prove a PASS candidate correct (FR-AGENT-07)",
    )
    p_formalize.add_argument("--run", required=True, help="run directory")
    p_formalize.add_argument("--candidate", required=True, help="candidate id, e.g. gen001_c01")
    p_formalize.add_argument("--model", default=None, help="override model id")
    p_formalize.add_argument("--opencode-path", default=None, help="override opencode binary path")
    p_formalize.add_argument("--fresh", action="store_true",
                             help="ignore any existing module and redo all stages from scratch")
    p_formalize.add_argument("--stage-timeout", type=int, default=2400,
                             help="per-stage agent timeout in seconds (default 2400)")
    p_formalize.add_argument("--hints", default=None,
                             help="path to a markdown file with proof-strategy hints "
                                  "appended to every stage task")

    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    try:
        return _dispatch(parser, args)
    except (ConfigError, RunReadError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def _dispatch(parser, args) -> int:
    if args.command == "configure":
        return cmd_configure(args)
    elif args.command == "start":
        return cmd_start(args)
    elif args.command == "status":
        return cmd_status(args)
    elif args.command == "resume":
        return cmd_resume(args)
    elif args.command == "export":
        return cmd_export(args)
    elif args.command == "history":
        return cmd_history(args)
    elif args.command == "control":
        return cmd_control(args)
    elif args.command == "events":
        return cmd_events(args)
    elif args.command == "ui":
        return cmd_ui(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command in ("init", "check", "finish", "skill", "packs"):
        return cmd_workspace(args)
    elif args.command == "formalize":
        if args.stage_timeout < 60:
            print("--stage-timeout must be at least 60 seconds")
            return 2
        from .formalize import run_formalize
        return run_formalize(
            Path(args.run),
            args.candidate,
            model=args.model,
            opencode_path=args.opencode_path,
            fresh=args.fresh,
            stage_timeout=args.stage_timeout,
            hints_path=args.hints,
        )
    else:
        parser.print_help()
        return 1


def cmd_configure(args) -> int:
    config = RunConfig(
        problem=args.problem,
        model=args.model,
        population_size=args.population,
        max_generations=args.generations,
        timeout_seconds=args.timeout,
        elitism_k=args.elitism_k,
        early_stop_on_success=not args.no_early_stop,
        workdir=args.workdir,
        bound=Bound(
            n_max=args.n_max,
            seq_len_max=args.seq_len,
            seq_count=args.seq_count,
            seed=args.seed,
        ),
    )
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  {e}")
        return 1
    config.save(args.output)
    print(f"Configuration saved to {args.output}")
    print(f"  Problem: {config.problem}")
    print(f"  Population: {config.population_size}")
    print(f"  Max generations: {config.max_generations}")
    print(f"  Timeout: {config.timeout_seconds}s")
    print(f"  Bound: n_max={config.bound.n_max}, seq_len={config.bound.seq_len_max}")
    return 0


def cmd_start(args) -> int:
    config = RunConfig.load(args.config)
    if args.model:
        config.model = args.model
    errors = config.validate()
    if errors:
        print("Configuration errors:")
        for e in errors:
            print(f"  {e}")
        return 1

    orch = Orchestrator(config=config, run_id=args.run_id)
    summary = orch.run()

    done = "stopped" if summary["stop_reason"] == "agent_unavailable" else "complete"
    print(f"\nRun {done}: {summary['run_id']}")
    print(f"  Stop reason: {summary['stop_reason']}")
    print(f"  Generations: {summary['generation']}")
    print(f"  Best fitness: {summary['best_fitness']:.2f}")
    if summary.get("best_candidate_id"):
        print(f"  Best candidate: {summary['best_candidate_id']}")
    print(f"  Model calls: {summary['model_calls']}")
    return _agent_status(summary)


def cmd_control(args) -> int:
    from .events import send_command, validate_command

    run_dir = Path(args.run_dir)
    if not (run_dir / "config.yaml").exists():
        print(f"Not a run directory: {run_dir}")
        return 1
    extra: dict = {}
    if args.cmd == "hint":
        extra["text"] = " ".join(args.args)
    elif args.cmd == "set":
        if len(args.args) != 2:
            print("usage: evoalgo control RUN set FIELD VALUE")
            return 2
        try:
            extra = {"field": args.args[0], "value": int(args.args[1])}
        except ValueError:
            print(f"VALUE must be an integer, got {args.args[1]!r}")
            return 2
    elif args.args:
        print(f"{args.cmd} takes no arguments")
        return 2
    error = validate_command({"cmd": args.cmd, **extra})
    if error:
        print(error)
        return 2
    record = send_command(run_dir, args.cmd, **extra)
    print(f"Queued {args.cmd} ({record['id']}); applied at the next generation boundary.")
    return 0


def cmd_ui(args) -> int:
    try:
        import uvicorn
        from .server import create_app
    except ImportError:
        print("The UI needs the 'ui' extra: pip install -e '.[ui]'")
        return 1
    runs = Path(args.runs)
    if not runs.is_dir():
        print(f"Run directory root not found: {runs}")
        return 1
    import secrets
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"WARNING: binding to {args.host}. The token is the only protection and "
              "travels in clear HTTP; prefer loopback plus an SSH port-forward.")
    token = secrets.token_urlsafe(32)
    link = f"http://{args.host}:{args.port}/?token={token}"
    print(f"evoalgo UI on http://{args.host}:{args.port} (runs: {runs.resolve()})", flush=True)
    if sys.stdout.isatty():
        print(f"open this link, it holds the access token:\n  {link}", flush=True)
    else:
        # stdout is a log file: keep the token out of it, in a file only the user can read.
        link_file = runs / ".ui-link"
        fd = os.open(link_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(link + "\n")
        print(f"the access link is in {link_file.resolve()} (mode 600)", flush=True)
    try:
        uvicorn.run(create_app(runs, token=token), host=args.host, port=args.port, log_level="warning")
    finally:
        if not sys.stdout.isatty():
            (runs / ".ui-link").unlink(missing_ok=True)  # the token dies with the server
    return 0


def cmd_events(args) -> int:
    from .events import backfill

    status = 0
    for d in args.run_dirs:
        try:
            n = backfill(Path(d), force=args.force)
        except FileExistsError as e:
            print(f"skip {d}: {e}")
            status = 1
            continue
        print(f"{d}: {n} events" if n else f"{d}: no generation checkpoints, nothing written")
    return status


def cmd_workspace(args) -> int:
    from . import workspace as wsm
    try:
        if args.command == "init":
            ws = wsm.init_workspace(args.pack, args.dir, runs_root=args.runs, run_id=args.run_id,
                                    goal=args.goal, harness=args.harness,
                                    max_checks=args.max_checks)
            print(json.dumps({"workspace": str(ws.dir), "run_dir": str(ws.run_dir),
                              "program": str(ws.dir / wsm.PROGRAM_FILE),
                              "candidate": str(ws.dir / wsm.CANDIDATE_FILE)}, indent=2))
            return 0
        if args.command == "packs":
            from .packs import find_packs, pack_info
            tiers = {"calibration": 0, "core": 1, "open": 2}
            packs = sorted(find_packs(), key=lambda p: (tiers.get(p.tier, 9), p.name))
            keep = ("name", "tier", "title", "directed", "update_mode", "question")
            print(json.dumps([{k: pack_info(p)[k] for k in keep} for p in packs], indent=1))
            return 0
        if args.command == "skill":
            dests = wsm.install_skill("project" if args.project else "user",
                                      Path(args.project) if args.project else None, args.force)
            print(json.dumps({"installed": [str(d) for d in dests]}, indent=2))
            return 0
        ws = wsm.Workspace.find(args.workspace)
        if args.command == "finish":
            print(json.dumps(wsm.finish(ws, args.reason), indent=2, default=str))
            return 0
        level = "full" if args.final else args.level
        report = wsm.check(ws, args.file, level=level, note=args.note, final=args.final)
        print(json.dumps(report, indent=1, default=str))
        return 0 if report["verdict"] == "PASS" else 3
    except KeyboardInterrupt:
        print(json.dumps({"error": "interrupted"}))
        return 130
    except Exception as e:  # agents parse stdout: always answer in JSON
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
        return 2


class RunReadError(Exception):
    """A run directory whose generation checkpoints cannot be read."""


def _committed_generation(run_dir: Path) -> int:
    """The last committed generation number; RunReadError if none or corrupt."""
    try:
        text = (run_dir / "COMMITTED").read_text().strip()
    except FileNotFoundError:
        raise RunReadError("No committed generations found.") from None
    except OSError as e:
        raise RunReadError(f"cannot read {run_dir / 'COMMITTED'}: {e.strerror}") from None
    if not text.isdigit():
        raise RunReadError(f"corrupt marker {run_dir / 'COMMITTED'}: {text[:40]!r}")
    return int(text)


def _read_generation(run_dir: Path, gen: int) -> dict | None:
    """One generation checkpoint as a dict, None if absent; RunReadError if corrupt."""
    path = run_dir / f"generation_{gen:04d}.json"
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        raise RunReadError(f"corrupt checkpoint {path}: {e}") from None


def cmd_status(args) -> int:
    run_dir = Path(args.run_dir)
    if getattr(args, "json", False):
        from .events import summarize
        if not (run_dir / "config.yaml").is_file():
            print(json.dumps({"error": f"no run at {run_dir}"}))
            return 1
        print(json.dumps(_run_summary(run_dir, summarize), indent=1, default=str))
        return 0
    gen_num = _committed_generation(run_dir)
    data = _read_generation(run_dir, gen_num)
    if data is None:
        raise RunReadError(f"Generation file missing: {run_dir / f'generation_{gen_num:04d}.json'}")
    candidates = data.get("candidates", [])
    best = max((c.get("fitness", 0) for c in candidates), default=0)
    passing = sum(1 for c in candidates if c.get("state") == "PASS")

    # Name the best candidate by the same ranking selection uses (passing,
    # then fitness, then lowest work_ratio), not just max fitness.
    from .population import _rank_key_dict
    ranked = sorted(
        (c for c in candidates if c.get("state")),
        key=_rank_key_dict,
    )
    top = ranked[0] if ranked else None
    if top is not None and top.get("work_ratio") is not None:
        top_str = f"{top['id']} (work_ratio={top['work_ratio']:.3f})"
    elif top is not None:
        top_str = top["id"]
    else:
        top_str = "--"

    print(f"Run: {data.get('run_id', '?')}")
    print(f"  Generation: {gen_num}")
    print(f"  Problem: {data.get('problem', '?')}")
    print(f"  Best fitness: {best:.2f}")
    print(f"  Best candidate: {top_str}")
    print(f"  Passing: {passing}/{len(candidates)}")
    print(f"  Candidates:")
    for c in candidates:
        fit = c.get("fitness", 0)
        state = c.get("state", "?")
        wr = c.get("work_ratio")
        wr_str = f"{wr:.2f}" if wr is not None else "--"
        print(f"    {c['id']}: {state} fitness={fit:.2f} work_ratio={wr_str} "
              f"tests={c.get('tests_passed', 0)}/{c.get('tests_total', 0)}")
    return 0


def cmd_resume(args) -> int:
    run_dir = Path(args.run_dir)
    config_path = run_dir / "config.yaml"
    if not config_path.exists():
        print(f"No config found at {config_path}")
        return 1

    if (run_dir / "HARNESS").exists():
        print(f"{run_dir} is driven by a coding agent (evoalgo init); continue it there "
              "with `evoalgo check`")
        return 1
    config = RunConfig.load(config_path)
    # Resume this directory, wherever it is: the saved workdir may be relative
    # to the cwd of the original start.
    config.workdir = str(run_dir.resolve().parent)
    orch = Orchestrator(config=config, run_id=run_dir.name)
    try:
        orch.checkpoint.load_latest()
    except (OSError, ValueError) as e:
        raise RunReadError(f"cannot resume {run_dir}: {e}") from None

    # Discard any incomplete generations
    removed = orch.checkpoint.discard_incomplete()
    if removed:
        print(f"Discarded incomplete generations: {removed}")

    summary = orch.run()
    done = "stopped" if summary["stop_reason"] == "agent_unavailable" else "completed"
    print(f"\nRun resumed and {done}: {summary['run_id']}")
    print(f"  Stop reason: {summary['stop_reason']}")
    print(f"  Generations: {summary['generation']}")
    print(f"  Best fitness: {summary['best_fitness']:.2f}")
    return _agent_status(summary)


def _agent_status(summary: dict) -> int:
    if summary.get("stop_reason") != "agent_unavailable":
        return 0
    print(f"error: the agent backend produced no candidate: {summary.get('agent_error')}",
          file=sys.stderr)
    return 1


def cmd_export(args) -> int:
    run_dir = Path(args.run_dir)
    results_dir = run_dir / "results"

    gen_num = _committed_generation(run_dir)
    all_candidates = []
    for g in range(1, gen_num + 1):
        data = _read_generation(run_dir, g)
        if data is not None:
            for c in data.get("candidates", []):
                c["generation"] = g
                all_candidates.append(c)

    # Best candidate: reuse the population ranking (passing, then fitness,
    # then lowest work_ratio) so the exported headline matches what selection
    # actually chose, instead of max-fitness + insertion order.
    from .population import _rank_key_dict

    ranked = sorted(
        (c for c in all_candidates if c.get("state")),
        key=_rank_key_dict,
    )
    best = ranked[0] if ranked else None

    # Write summary
    summary = {
        "run_id": run_dir.name,
        "total_generations": gen_num,
        "total_candidates": len(all_candidates),
        "best_fitness": best.get("fitness", 0) if best else 0,
        "best_candidate_id": best.get("id") if best else None,
        "best_work_ratio": best.get("work_ratio") if best else None,
        "passing": sum(1 for c in all_candidates if c.get("state") == "PASS"),
    }

    results_dir.mkdir(exist_ok=True)
    (results_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )

    # CSV
    csv_lines = ["candidate_id,generation,fitness,work_ratio,state,timeout,tests_passed,tests_total"]
    for c in all_candidates:
        csv_lines.append(
            f"{c['id']},{c['generation']},{c.get('fitness', 0)},"
            f"{c.get('work_ratio', '')},{c['state']},"
            f"{c.get('timeout', False)},{c.get('tests_passed', 0)},"
            f"{c.get('tests_total', 0)}"
        )
    (results_dir / "efficiency_report.csv").write_text("\n".join(csv_lines))

    print(f"Exported to {results_dir}/")
    print(f"  run_summary.json ({len(all_candidates)} candidates, {gen_num} generations)")
    print(f"  efficiency_report.csv")
    return 0


def _run_summary(run_dir: Path, summarize) -> dict:
    """Event summary plus the final grade and best candidate path, for agents."""
    from .events import read_events
    s = summarize(run_dir)
    s.pop("history", None)
    final = next((e for e in reversed(read_events(run_dir)) if e.get("type") == "final_graded"), None)
    if final:
        s["final_grade"] = {k: final.get(k) for k in ("id", "state", "tests_passed", "tests_total",
                                                      "work_ratio", "n_max")}
    best = (final or {}).get("id") if final and final.get("state") == "PASS" else s.get("best_id")
    if best and (run_dir / "candidates" / f"{best}.py").is_file():
        s["best_candidate_path"] = str(run_dir / "candidates" / f"{best}.py")
    s["harness"] = (run_dir / "HARNESS").exists()
    return s


def cmd_history(args) -> int:
    workdir = Path(args.workdir)
    if not workdir.exists():
        print(f"No runs directory: {workdir}")
        return 1
    if getattr(args, "json", False):
        from .events import summarize
        runs = [_run_summary(p.parent, summarize) for p in sorted(workdir.glob("*/config.yaml"))]
        runs.sort(key=lambda r: r.get("updated") or "", reverse=True)
        print(json.dumps(runs, indent=1, default=str))
        return 0

    runs = sorted(workdir.iterdir())
    if not runs:
        print("No runs found.")
        return 0

    print(f"{'Run ID':<30} {'Gen':>5} {'Best':>6} {'BestWR':>7} {'Pass':>5} {'Problem':<15}")
    print("-" * 73)
    for run_dir in runs:
        if not run_dir.is_dir():
            continue
        try:
            gen_num = _committed_generation(run_dir)
            data = _read_generation(run_dir, gen_num)
        except RunReadError:
            continue  # not a run, or unreadable: history lists the rest
        if data is None:
            continue
        candidates = data.get("candidates", [])
        best = max((c.get("fitness", 0) for c in candidates), default=0)
        passing = sum(1 for c in candidates if c.get("state") == "PASS")
        pass_wrs = [c["work_ratio"] for c in candidates
                    if c.get("state") == "PASS" and c.get("work_ratio") is not None]
        best_wr_str = f"{min(pass_wrs):.3f}" if pass_wrs else "--"
        problem = data.get("problem", "?")
        print(f"{run_dir.name:<30} {gen_num:>5} {best:>6.2f} {best_wr_str:>7} {passing:>5} {problem:<15}")
    return 0


def cmd_verify(args) -> int:
    """Run the verifier self-test (FR-VER-08) for a problem with a fault corpus.

    The known-good reference and every equivalent control must PASS, and every
    seeded fault must be rejected (FAIL or CRASH). Exit code 0 only if all hold.
    """
    from .problem_definitions import get_problem
    from .selftest.references import CORPUS_PROBLEMS

    if args.problem not in CORPUS_PROBLEMS:
        print(f"no fault corpus for {args.problem}; the self-test covers "
              f"{', '.join(CORPUS_PROBLEMS)}", file=sys.stderr)
        return 2
    problem = get_problem(args.problem)
    with tempfile.TemporaryDirectory(prefix="evoalgo_verify_") as tmp:
        n_max = 5 if args.n_max is None else args.n_max
        return _cmd_verify_corpus(problem, n_max, args, tmpdir=Path(tmp))


def _make_selftest_verifier(problem, n_max: int, args) -> Verifier:
    from .sandbox import Sandbox
    from .verifier import Verifier

    sandbox = Sandbox(timeout_seconds=args.timeout, directed=problem.directed)
    return Verifier(
        problem=problem,
        sandbox=sandbox,
        bound_n_max=n_max,
        bound_n_random=0,
        bound_seq_len_max=10,
        bound_seq_count=3,
        bound_seed=42,
        use_offline=False,
        relabels_per_class=args.relabels,
        chunk_size=args.chunk_size,
        workers=args.workers,
    )


def _run_candidate(verifier: "Verifier", code: str, name: str, tmpdir: Path) -> tuple:
    """Write ``code`` to a temp candidate file, verify it, return
    (state, fitness, wall_seconds)."""
    from .candidate import Candidate

    path = tmpdir / f"{name}.py"
    path.write_text(code)
    cand = Candidate(id=name, code_path=str(path), generation=0)
    t0 = time.time()
    result = verifier.verify(cand)
    wall = time.time() - t0
    return cand.state.value, result.fitness, wall


def _cmd_verify_corpus(problem, n_max: int, args, tmpdir: Path) -> int:
    """Full exhaustive self-test for a corpus problem (BFS/DFS/LBFS)."""
    from .selftest.references import reference_code
    from .selftest.faults import (
        compose_fault_code,
        equivalent_controls,
        real_faults,
    )

    print(f"Verifier self-test for problem: {problem.name}")
    print(f"  n_max={n_max}  relabels/class={args.relabels}  "
          f"chunk_size={args.chunk_size or 'auto'}  workers={args.workers or 'auto'}  "
          f"per-chunk timeout={args.timeout}s")

    verifier = _make_selftest_verifier(problem, n_max, args)
    counts = verifier.test_counts()
    print(f"  base test graphs per n: {counts}  (total {sum(counts.values())})")

    rows: list[tuple[str, str, str, float, bool]] = []  # (name, kind, state, wall, ok)

    def record(name, kind, code, expect):
        state, fitness, wall = _run_candidate(verifier, code, name, tmpdir)
        if expect == "PASS":
            ok = state == "PASS"
        else:  # expect FAIL/CRASH
            ok = state in ("FAIL", "CRASH")
        rows.append((name, kind, state, wall, ok))
        print(f"  {name:<24} {kind:<10} state={state:<6} "
              f"fitness={fitness:.3f} wall={wall:6.1f}s  {'OK' if ok else 'UNEXPECTED'}")

    # 1. known-good reference must PASS
    print("\n  [known-good] validate-or-rebuild reference (must PASS)")
    record("known-good", "reference", reference_code(problem.name), "PASS")

    if problem.name == "dynamic_dfs":
        # 1b. Yang et al. fully dynamic DFS (Algorithms 2-5) must PASS, and
        # every one-line mutation of it must be rejected.
        from .selftest.references import YANG_DFS_CODE, YANG_DFS_MUTATIONS, yang_mutation_code
        print("\n  [known-good] Yang et al. dynamic DFS, Algorithms 2-5 (must PASS)")
        record("yang-dfs", "reference", YANG_DFS_CODE, "PASS")
        print("\n  [faults] mutations of the Yang reference (must FAIL/CRASH)")
        for m in YANG_DFS_MUTATIONS:
            record(f"yang_{m['id']}", "fault", yang_mutation_code(m), "FAIL")

    # 2. every real fault must be REJECTED (FAIL/CRASH)
    print("\n  [faults] seeded real faults (must FAIL/CRASH)")
    for fault in real_faults(problem.name):
        record(f"fault_{fault['id']}", "fault", compose_fault_code(problem.name, fault), "FAIL")

    # 3. every equivalent control must be ACCEPTED (PASS)
    print("\n  [controls] equivalent valid variants (must PASS)")
    for ctrl in equivalent_controls(problem.name):
        record(f"control_{ctrl['id']}", "control", compose_fault_code(problem.name, ctrl), "PASS")

    # Summary table
    print("\n  Summary:")
    print(f"  {'candidate':<24} {'kind':<10} {'state':<6} {'wall(s)':>8}  expected")
    print("  " + "-" * 64)
    for name, kind, state, wall, ok in rows:
        expected = "PASS" if kind in ("reference", "control") else "FAIL/CRASH"
        mark = "ok" if ok else "** UNEXPECTED **"
        print(f"  {name:<24} {kind:<10} {state:<6} {wall:>8.1f}  {expected}  {mark}")

    # Zero-false-negative verdict: every real fault rejected.
    real_fault_rows = [r for r in rows if r[1] == "fault"]
    rejected = sum(1 for r in real_fault_rows if r[4])
    n_real = len(real_fault_rows)
    zero_fn = (rejected == n_real) and n_real > 0
    known_good_ok = all(r[4] for r in rows if r[1] == "reference")
    controls_ok = all(r[4] for r in rows if r[1] == "control")

    print("\n  Zero-false-negative (n<=%d): %d/%d real faults rejected -> %s"
          % (n_max, rejected, n_real, "PASS" if zero_fn else "FAIL"))
    print(f"  Known-good accepted: {'PASS' if known_good_ok else 'FAIL'}")
    print(f"  Equivalent controls accepted: {'PASS' if controls_ok else 'FAIL'}")

    all_ok = zero_fn and known_good_ok and controls_ok
    print("\n  Verifier self-test: " + ("ALL PASS" if all_ok else "FAILED"))
    return 0 if all_ok else 1


def _generate_known_good_candidate(problem_name: str) -> str:
    """Generate a known-good candidate that recomputes from scratch.

    Each problem gets its own offline algorithm embedded in the candidate.
    """
    algorithms = {
        "dynamic_bfs": _BFS_CODE,
        "dynamic_dfs": _DFS_CODE,
        "dynamic_mcs": _MCS_CODE,
        "dynamic_lbfs": _LBFS_CODE,
        "dynamic_scc": _SCC_CODE,
        "reachability": _REACH_CODE,
    }
    if problem_name not in algorithms:
        raise ValueError(f"no known-good recompute candidate for {problem_name!r}")
    algo = algorithms.get(problem_name, _BFS_CODE)
    return f'''# Known-good candidate: recompute from scratch after each update
# Problem: {problem_name}

def init(graph):
    return _compute(graph)

def insert_edge(graph, edge, state):
    return _compute(graph)

def delete_edge(graph, edge, state):
    return _compute(graph)

{algo}
'''


def _generate_known_bad_candidate(problem_name: str) -> str:
    """Generate a deliberately faulty candidate."""
    return f'''# Known-bad candidate: deliberately wrong (returns stale state)
# Problem: {problem_name}

def init(graph):
    return {{"_stale": True}}

def insert_edge(graph, edge, state):
    # Bug: does nothing
    return state

def delete_edge(graph, edge, state):
    # Bug: does nothing
    return state
'''


_BFS_CODE = '''
def _compute(graph):
    """BFS from vertex 0."""
    import collections
    n = len(graph)
    root = 0
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
'''


_DFS_CODE = '''
def _compute(graph):
    """DFS from vertex 0 with discovery/finish times."""
    n = len(graph)
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]

    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1

    dfs(0)
    return {"parent": parent, "discover": discover, "finish": finish}
'''


_MCS_CODE = '''
def _compute(graph):
    """Maximal Cardinality Search ordering."""
    n = len(graph)
    chosen = set()
    cardinality = {v: 0 for v in range(n)}
    ordering = []

    for _ in range(n):
        unchosen = [u for u in range(n) if u not in chosen]
        if not unchosen:
            break
        max_card = max(cardinality[u] for u in unchosen)
        candidates = [u for u in unchosen if cardinality[u] == max_card]
        v = min(candidates)
        ordering.append(v)
        chosen.add(v)
        for u in range(n):
            if graph[v][u] == 1 and u not in chosen:
                cardinality[u] += 1

    return {"ordering": ordering}
'''


_LBFS_CODE = '''
def _compute(graph):
    """Lexicographic BFS by partition refinement (start 0, min-id ties)."""
    n = len(graph)
    cells = [list(range(n))] if n else []
    ordering = []
    while cells:
        pivot = cells[0].pop(0)
        ordering.append(pivot)
        refined = []
        for cell in cells:
            inside = [u for u in cell if graph[pivot][u]]
            outside = [u for u in cell if not graph[pivot][u]]
            refined.extend(c for c in (inside, outside) if c)
        cells = refined
    return {"ordering": ordering}
'''


_SCC_CODE = '''
def _compute(graph):
    """Tarjan SCC."""
    n = len(graph)
    index_counter = [0]
    stack = []
    lowlink = [0] * n
    index = [0] * n
    on_stack = [False] * n
    visited = [False] * n
    result = []

    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True
        visited[v] = True

        for w in range(n):
            if graph[v][w] == 1:
                if not visited[w]:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif on_stack[w]:
                    lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                comp.append(w)
                if w == v:
                    break
            result.append(comp)

    for v in range(n):
        if not visited[v]:
            strongconnect(v)

    return {"components": result}
'''


_REACH_CODE = '''
def _compute(graph):
    """Reachability from vertex 0."""
    import collections
    n = len(graph)
    root = 0
    visited = {root}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                visited.add(v)
                queue.append(v)
    return {"reachable": sorted(visited)}
'''


if __name__ == "__main__":
    sys.exit(main())
