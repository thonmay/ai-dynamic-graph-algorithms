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
import sys
from pathlib import Path

from .config import RunConfig, Bound, VALID_PROBLEMS
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
    p_start.add_argument("--model", default=None, help="override model id (e.g. ericai/zai-org/GLM-5.2-FP8)")

    # run status
    p_status = subparsers.add_parser("status", help="show current run status")
    p_status.add_argument("run_dir", help="path to run directory")

    # run resume
    p_resume = subparsers.add_parser("resume", help="resume from last checkpoint")
    p_resume.add_argument("run_dir", help="path to run directory")

    # run export
    p_export = subparsers.add_parser("export", help="export run results")
    p_export.add_argument("run_dir", help="path to run directory")

    # run history
    p_history = subparsers.add_parser("history", help="list previous runs")
    p_history.add_argument("--workdir", default="runs", help="run directory root")

    # verify (self-test)
    p_verify = subparsers.add_parser("verify", help="run verifier self-test (FR-VER-08)")
    p_verify.add_argument("--problem", choices=sorted(VALID_PROBLEMS), default="dynamic_bfs")
    p_verify.add_argument("--n-max", type=int, default=4, help="max graph size for self-test")

    # formalize (Lean proof of a PASS candidate)
    p_formalize = subparsers.add_parser(
        "formalize",
        help="dispatch lean-prover agent to prove a PASS candidate correct (FR-AGENT-07)",
    )
    p_formalize.add_argument("--run", required=True, help="run directory")
    p_formalize.add_argument("--candidate", required=True, help="candidate id, e.g. gen001_c01")
    p_formalize.add_argument("--model", default=None, help="override model id")
    p_formalize.add_argument("--enlcode-path", default=None, help="override enlcode binary path")
    p_formalize.add_argument("--fresh", action="store_true",
                             help="ignore any existing module and redo all stages from scratch")
    p_formalize.add_argument("--stage-timeout", type=int, default=2400,
                             help="per-stage agent timeout in seconds (default 2400)")
    p_formalize.add_argument("--hints", default=None,
                             help="path to a markdown file with proof-strategy hints "
                                  "appended to every stage task")

    args = parser.parse_args(argv)
    setup_logging(args.verbose)

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
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "formalize":
        if args.stage_timeout < 60:
            print("--stage-timeout must be at least 60 seconds")
            return 2
        from .formalize import run_formalize
        return run_formalize(
            Path(args.run),
            args.candidate,
            model=args.model,
            enlcode_path=args.enlcode_path,
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

    print(f"\nRun complete: {summary['run_id']}")
    print(f"  Stop reason: {summary['stop_reason']}")
    print(f"  Generations: {summary['generation']}")
    print(f"  Best fitness: {summary['best_fitness']:.2f}")
    if summary.get("best_candidate_id"):
        print(f"  Best candidate: {summary['best_candidate_id']}")
    print(f"  Model calls: {summary['model_calls']}")
    return 0


def cmd_status(args) -> int:
    run_dir = Path(args.run_dir)
    committed = run_dir / "COMMITTED"
    if not committed.exists():
        print("No committed generations found.")
        return 1

    gen_num = int(committed.read_text().strip())
    gen_file = run_dir / f"generation_{gen_num:04d}.json"
    if not gen_file.exists():
        print(f"Generation file missing: {gen_file}")
        return 1

    data = json.loads(gen_file.read_text())
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

    config = RunConfig.load(config_path)
    run_id = run_dir.name
    orch = Orchestrator(config=config, run_id=run_id)

    # Discard any incomplete generations
    removed = orch.checkpoint.discard_incomplete()
    if removed:
        print(f"Discarded incomplete generations: {removed}")

    summary = orch.run()
    print(f"\nRun resumed and completed: {summary['run_id']}")
    print(f"  Stop reason: {summary['stop_reason']}")
    print(f"  Generations: {summary['generation']}")
    print(f"  Best fitness: {summary['best_fitness']:.2f}")
    return 0


def cmd_export(args) -> int:
    run_dir = Path(args.run_dir)
    results_dir = run_dir / "results"

    # Find the latest generation
    committed = run_dir / "COMMITTED"
    if not committed.exists():
        print("No committed generations found.")
        return 1

    gen_num = int(committed.read_text().strip())

    # Collect all generation data
    all_candidates = []
    for g in range(1, gen_num + 1):
        gen_file = run_dir / f"generation_{g:04d}.json"
        if gen_file.exists():
            data = json.loads(gen_file.read_text())
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


def cmd_history(args) -> int:
    workdir = Path(args.workdir)
    if not workdir.exists():
        print(f"No runs directory: {workdir}")
        return 1

    runs = sorted(workdir.iterdir())
    if not runs:
        print("No runs found.")
        return 0

    print(f"{'Run ID':<30} {'Gen':>5} {'Best':>6} {'BestWR':>7} {'Pass':>5} {'Problem':<15}")
    print("-" * 73)
    for run_dir in runs:
        if not run_dir.is_dir():
            continue
        committed = run_dir / "COMMITTED"
        try:
            if not committed.exists():
                continue
            gen_num = int(committed.read_text().strip())
            gen_file = run_dir / f"generation_{gen_num:04d}.json"
            if not gen_file.exists():
                continue
            data = json.loads(gen_file.read_text())
        except (OSError, ValueError):
            # Skip unreadable or malformed run dirs (e.g. a non-run dir under
            # the workdir that happens to contain a COMMITTED file).
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
    """Run verifier self-test (FR-VER-08).

    Tests the verifier against:
    (a) a known-good reference algorithm (offline algorithm wrapped as candidate)
    (b) a known-bad mutation (deliberately faulty)
    """
    from .problem_definitions import get_problem
    from .sandbox import Sandbox
    from .verifier import Verifier
    from .candidate import Candidate

    print(f"Verifier self-test for problem: {args.problem}")
    print(f"  n_max={args.n_max}")

    problem = get_problem(args.problem)
    sandbox = Sandbox(timeout_seconds=30, directed=problem.directed)
    verifier = Verifier(
        problem=problem,
        sandbox=sandbox,
        bound_n_max=args.n_max,
        bound_n_random=5,
        bound_seq_len_max=10,
        bound_seq_count=3,
        bound_seed=42,
    )

    # Write a known-good candidate (wraps the offline algorithm)
    import tempfile
    tmpdir = Path(tempfile.mkdtemp(prefix="evoalgo_verify_"))

    good_code = _generate_known_good_candidate(args.problem)
    good_path = tmpdir / "known_good.py"
    good_path.write_text(good_code)

    bad_code = _generate_known_bad_candidate(args.problem)
    bad_path = tmpdir / "known_bad.py"
    bad_path.write_text(bad_code)

    results: list[tuple[str, bool, str]] = []

    # Test known-good
    print("\n  Testing known-good candidate...")
    good_candidate = Candidate(id="test_good", code_path=str(good_path), generation=0)
    good_result = verifier.verify(good_candidate)
    good_pass = good_candidate.state.value == "PASS"
    results.append(("known-good", good_pass, good_candidate.state.value))
    print(f"    State: {good_candidate.state.value}, Fitness: {good_result.fitness:.2f}")

    # Test known-bad
    print("  Testing known-bad candidate...")
    bad_candidate = Candidate(id="test_bad", code_path=str(bad_path), generation=0)
    bad_result = verifier.verify(bad_candidate)
    bad_rejected = bad_candidate.state.value in ("FAIL", "CRASH")
    results.append(("known-bad", bad_rejected, bad_candidate.state.value))
    print(f"    State: {bad_candidate.state.value}, Fitness: {bad_result.fitness:.2f}")

    # Summary
    print("\n  Results:")
    all_pass = True
    for name, passed, state in results:
        status = "PASS" if passed else "FAIL"
        print(f"    {name}: {status} (state={state})")
        if not passed:
            all_pass = False

    if all_pass:
        print("\n  Verifier self-test: ALL PASS")
        return 0
    else:
        print("\n  Verifier self-test: FAILED")
        return 1


def _generate_known_good_candidate(problem_name: str) -> str:
    """Generate a known-good candidate that recomputes from scratch.

    Each problem gets its own offline algorithm embedded in the candidate.
    """
    algorithms = {
        "dynamic_bfs": _BFS_CODE,
        "dynamic_dfs": _DFS_CODE,
        "dynamic_mcs": _MCS_CODE,
        "dynamic_scc": _SCC_CODE,
        "reachability": _REACH_CODE,
    }
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
