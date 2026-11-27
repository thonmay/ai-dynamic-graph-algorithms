# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Benchmark final candidates on graphs larger than the exhaustive bound.

    python scripts/bench.py campaign/eval1.yaml [--sizes 16 64 128] [--graphs 10] [--updates 200]

For every campaign run whose final grade passed, times the candidate against
the recompute-from-scratch candidate (same lists-of-lists representation, so
the comparison is not skewed by numpy overhead) on random graphs and random
single-edge updates, and checks the invariant on a sample of steps: a spot
check of correctness beyond n <= 5, where the verifier is exhaustive.

Each (run, size) cell runs in the sandbox jail (candidates are untrusted
code) under a wall-clock budget (--cell-timeout); a slower candidate is
reported as a timeout. Writes <out>/bench.csv (one row per run and size), or
--csv PATH (a live demo should not overwrite the committed table).
Updates are balanced (half inserts of missing edges, half deletes of
existing edges), so the density stays at the start value.
Speedup = recompute time / candidate time over all updates (> 1 is faster).
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from evoalgo.cli import _generate_known_good_candidate  # noqa: E402
from evoalgo.problem_definitions import get_problem  # noqa: E402

CHECK_EVERY = 10          # invariant check on every 10th update
CHECK_N_MAX = {"dynamic_lbfs": 64, "dynamic_mcs": 64}  # O(n^3) checkers


def random_graph(rng: random.Random, n: int, directed: bool, avg_deg: float) -> list[list[int]]:
    p = min(1.0, avg_deg / max(1, n - 1))
    g = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in range(n) if directed else range(u + 1, n):
            if u != v and rng.random() < p:
                g[u][v] = 1
                if not directed:
                    g[v][u] = 1
    return g


def run_sequence(mod, graph: list[list[int]], ops: list[tuple[str, int, int]], directed: bool,
                 problem, check: bool) -> tuple[int, str | None]:
    """Total ns spent in the module's update calls; first invariant failure if any."""
    g = [row[:] for row in graph]
    state = mod.init(g)
    total = 0
    for i, (kind, u, v) in enumerate(ops):
        val = 1 if kind == "insert" else 0
        g[u][v] = val
        if not directed:
            g[v][u] = val
        fn = mod.insert_edge if kind == "insert" else mod.delete_edge
        t0 = time.perf_counter_ns()
        state = fn(g, (u, v), state)
        total += time.perf_counter_ns() - t0
        # Every CHECK_EVERY-th state, and always the last one.
        if check and (i % CHECK_EVERY == 0 or i == len(ops) - 1):
            try:
                ok = problem.check_invariant(copy.deepcopy(state), np.array(g), 0 if problem.needs_root else None)
            except Exception as e:
                ok, why = False, f"{type(e).__name__}"
            else:
                why = None
            if not ok:
                return total, f"step {i}: {kind} ({u},{v}) {why or 'invariant violated'}"
    return total, None


def random_ops(rng: random.Random, graph: list[list[int]], n: int, count: int,
               directed: bool) -> list[tuple[str, int, int]]:
    """Balanced updates: each step inserts a missing edge or deletes an
    existing one with equal probability, so density stays near the start
    value. (Uniform random pairs on a sparse graph are ~90% inserts, which
    densifies the graph and makes most updates trivial.)"""
    g = [row[:] for row in graph]
    pairs = [(u, v) for u in range(n) for v in range(n)
             if u != v and (directed or u < v)]
    present = {p for p in pairs if g[p[0]][p[1]]}
    absent = [p for p in pairs if p not in present]
    present = list(present)
    ops = []
    for _ in range(count):
        delete = present and (not absent or rng.random() < 0.5)
        src, dst = (present, absent) if delete else (absent, present)
        i = rng.randrange(len(src))
        u, v = src[i]
        src[i] = src[-1]
        src.pop()
        dst.append((u, v))
        ops.append(("delete" if delete else "insert", u, v))
    return ops


def bench_cell(cand_code: str, ref_code: str, pack: str, n: int, graphs: int, updates: int,
               avg_deg: float, seed: int) -> dict:
    """One (candidate, size) cell. Runs inside the sandbox jail: the candidate
    is untrusted code. Same graphs and updates for every run of a problem."""
    import types
    problem = get_problem(pack)

    def module(code: str, name: str):
        mod = types.ModuleType(name)
        exec(compile(code, name, "exec"), mod.__dict__)
        return mod

    cand, ref = module(cand_code, "candidate"), module(ref_code, "reference")
    rng = random.Random(f"{seed}:{pack}:{n}")
    check = n <= CHECK_N_MAX.get(pack, 10**9)
    t_cand = t_ref = 0
    failure = None
    for _ in range(graphs):
        g = random_graph(rng, n, problem.directed, avg_deg)
        ops = random_ops(rng, g, n, updates, problem.directed)
        try:
            tc, failure = run_sequence(cand, g, ops, problem.directed, problem, check)
        except Exception as e:  # a crash beyond the exhaustive bound is a finding
            tc, failure = 0, f"crash {type(e).__name__}: {str(e)[:80]}"
        tr, _ = run_sequence(ref, g, ops, problem.directed, problem, False)
        t_cand, t_ref = t_cand + tc, t_ref + tr
        if failure:
            break
    return {"checked": check, "failure": failure, "t_cand": t_cand, "t_ref": t_ref}


CELL_MAIN = """
import json, sys
sys.path.insert(0, {scripts!r}); sys.path.insert(0, {src!r})
import bench
a = json.load(sys.stdin)
print(json.dumps(bench.bench_cell(**a)))
"""


def run_cell(args: dict, timeout: int) -> dict:
    """bench_cell in the jail, with a wall-clock budget."""
    import subprocess
    from evoalgo.sandbox import jailed_python
    prefix, env = jailed_python(readonly=(str(REPO / "src"), str(REPO / "scripts")))
    src = CELL_MAIN.format(scripts=str(REPO / "scripts"), src=str(REPO / "src"))
    try:
        proc = subprocess.run(prefix + ["-I", "-B", "-c", src], input=json.dumps(args),
                              capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {"checked": None, "failure": f"timeout ({timeout}s)", "t_cand": 0, "t_ref": 0}
    try:
        if proc.returncode != 0:
            raise ValueError(proc.stderr.strip()[-200:])
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError) as e:
        return {"checked": None, "failure": f"error: {e}"[:250], "t_cand": 0, "t_ref": 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--sizes", type=int, nargs="+", default=[16, 64, 128])
    ap.add_argument("--graphs", type=int, default=10)
    ap.add_argument("--updates", type=int, default=200)
    ap.add_argument("--avg-degree", type=float, default=3.0)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--cell-timeout", type=int, default=600,
                    help="seconds per (run, size); slower candidates are reported as timeouts")
    ap.add_argument("--csv", type=Path, help="output file (default: <plan out>/bench.csv)")
    args = ap.parse_args()
    plan = yaml.safe_load(Path(args.plan).read_text())
    out = REPO / plan["out"]
    results = list(csv.DictReader(open(out / "results.csv")))
    passed = [r for r in results if r.get("final_pass") == "True" and r.get("final_id")]
    total = args.graphs * args.updates
    rows = []
    for r in passed:
        pack = r["pack"]
        path = REPO / "runs" / r["run_id"] / "candidates" / f"{r['final_id']}.py"
        if not path.is_file():
            print(f"skip {r['run_id']}: no snapshot {path.name}", file=sys.stderr)
            continue
        code = path.read_text()
        ref = _generate_known_good_candidate(pack)
        for n in args.sizes:
            res = run_cell({"cand_code": code, "ref_code": ref, "pack": pack, "n": n,
                            "graphs": args.graphs, "updates": args.updates,
                            "avg_deg": args.avg_degree, "seed": args.seed}, args.cell_timeout)
            ok = res["t_cand"] and not res["failure"]
            row = {"run_id": r["run_id"], "mode": r["mode"], "pack": pack, "seed": r["seed"], "n": n,
                   "updates": total, "checked": res["checked"], "failure": res["failure"],
                   "speedup": round(res["t_ref"] / res["t_cand"], 2) if ok else None,
                   "cand_us_per_update": round(res["t_cand"] / 1000 / total, 2) if ok else None,
                   "recompute_us_per_update": round(res["t_ref"] / 1000 / total, 2) if ok else None}
            rows.append(row)
            print(json.dumps(row), flush=True)
    with open(args.csv or out / "bench.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["run_id"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
