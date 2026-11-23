#!/usr/bin/env python3
# AI-assisted code: generated and revised with Qwen3.8-Flash-Next
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""High-n cross-check for the proven dynamic-MCS candidate.

The verifier tests n <= 5 and the Lean proof covers its encoding, not this
Python file. This runs the actual candidate on large random graphs and after
every edge flip checks that its ordering is (1) a valid MCS ordering and (2)
equal to the offline MCS with lowest-id tie-break. Exits non-zero on the first
failure.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

import numpy as np


def load_candidate(path: Path):
    """The candidate as a module; its source comes from stdin when this
    script runs re-executed inside the sandbox jail (see main)."""
    import types
    src = sys.stdin.read() if os.environ.get("_EVOALGO_IN_JAIL") else path.read_text()
    mod = types.ModuleType("candidate")
    exec(compile(src, str(path), "exec"), mod.__dict__)
    for fn in ("init", "insert_edge", "delete_edge"):
        if not hasattr(mod, fn):
            raise AttributeError(f"candidate missing {fn}")
    return mod


def offline_mcs(graph: np.ndarray) -> list[int]:
    """From-scratch deterministic MCS (the oracle)."""
    n = graph.shape[0]
    chosen: set[int] = set()
    card = [0] * n
    order: list[int] = []
    for _ in range(n):
        unchosen = [u for u in range(n) if u not in chosen]
        if not unchosen:
            break
        max_card = max(card[u] for u in unchosen)
        v = min(u for u in unchosen if card[u] == max_card)
        order.append(v)
        chosen.add(v)
        for u in range(n):
            if graph[v, u] == 1 and u not in chosen:
                card[u] += 1
    return order


def is_valid_mcs(graph: np.ndarray, order: list[int]) -> bool:
    """Independent validity check: each pick is a maximal-cardinality vertex."""
    n = graph.shape[0]
    if len(order) != n or set(order) != set(range(n)):
        return False
    chosen: set[int] = set()
    card = [0] * n
    for v in order:
        unchosen = [u for u in range(n) if u not in chosen]
        if not unchosen:
            return False
        max_card = max(card[u] for u in unchosen)
        if card[v] != max_card:
            return False
        chosen.add(v)
        for u in range(n):
            if graph[v, u] == 1 and u not in chosen:
                card[u] += 1
    return True


def graph_to_matrix(graph: list[list[int]]) -> np.ndarray:
    return np.array(graph, dtype=np.int8)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", default="runs/mcs_dsv4f_dryrun/candidates/gen001_c01.py")
    ap.add_argument("--nmax", type=int, default=200)
    ap.add_argument("--nmin", type=int, default=6)
    ap.add_argument("--graphs-per-n", type=int, default=8)
    ap.add_argument("--flips-per-graph", type=int, default=40)
    ap.add_argument("--edge-prob", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=20260919)
    args = ap.parse_args()

    cand_path = Path(args.candidate)
    if not os.environ.get("_EVOALGO_IN_JAIL"):
        # The candidate is LLM-written: re-run this script in the sandbox jail.
        if not cand_path.exists():
            print(f"candidate not found: {cand_path}", file=sys.stderr)
            return 2
        import subprocess
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from evoalgo.sandbox import jailed_python
        script = Path(__file__).resolve()
        prefix, env = jailed_python(readonly=(str(script.parent),))
        env["_EVOALGO_IN_JAIL"] = "1"
        return subprocess.run(prefix + ["-I", "-B", str(script), *sys.argv[1:]],
                              input=cand_path.read_text(), text=True, env=env).returncode
    cand = load_candidate(cand_path)
    rng = random.Random(args.seed)

    total_checks = 0
    total_flips = 0
    ns = list(range(args.nmin, args.nmax + 1, max(1, (args.nmax - args.nmin) // 12)))
    if args.nmax not in ns:
        ns.append(args.nmax)

    for n in ns:
        for g in range(args.graphs_per_n):
            # random undirected graph as adjacency matrix
            adj = np.zeros((n, n), dtype=np.int8)
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < args.edge_prob:
                        adj[i, j] = adj[j, i] = 1
            init_graph = adj.tolist()

            state = cand.init(init_graph)
            if not is_valid_mcs(adj, state["ordering"]):
                print(f"FAIL init: n={n} graph#{g} produced invalid MCS ordering")
                return 1
            if state["ordering"] != offline_mcs(adj):
                print(f"FAIL init exact: n={n} graph#{g} != from-scratch MCS")
                return 1
            total_checks += 1

            for f in range(args.flips_per_graph):
                u = rng.randrange(n)
                v = rng.randrange(n)
                if u == v:
                    continue
                op = "insert" if rng.random() < 0.5 else "delete"
                if op == "insert":
                    adj[u, v] = adj[v, u] = 1
                    state = cand.insert_edge(graph_to_matrix(adj).tolist(), (u, v), state)
                else:
                    adj[u, v] = adj[v, u] = 0
                    state = cand.delete_edge(graph_to_matrix(adj).tolist(), (u, v), state)
                total_flips += 1

                if not is_valid_mcs(adj, state["ordering"]):
                    print(f"FAIL: n={n} graph#{g} flip#{f} {op} ({u},{v}) -> invalid MCS")
                    print(f"  ordering={state['ordering']}")
                    return 1
                if state["ordering"] != offline_mcs(adj):
                    print(f"FAIL exact: n={n} graph#{g} flip#{f} {op} ({u},{v}) != from-scratch MCS")
                    print(f"  dynamic ={state['ordering']}")
                    print(f"  offline ={offline_mcs(adj)}")
                    return 1
                total_checks += 1

        print(f"  n<= {n:>3}: {total_checks} checks, {total_flips} flips, all valid + exact")

    print(f"\nPASS: {total_checks} invariant checks, {total_flips} edge flips, "
          f"n up to {args.nmax}. Candidate matches from-scratch MCS exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
