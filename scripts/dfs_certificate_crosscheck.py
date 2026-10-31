# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Exhaustive n <= 4 cross-check of the DFS certificate checker.

Ground truth: a certificate (parent, discover, finish) restricted to the vertices
reachable from root 0 is valid iff some DFS from 0 (some neighbour order at every
vertex) produces exactly it. For every labelled digraph with n <= 4 we enumerate
all DFS runs (the set V of valid certificates) and a candidate set C: every
valid certificate plus, for each, all single-field perturbations (one parent
re-pointed to any other reachable vertex or None; one pair of times swapped).
The checker must accept exactly C intersect V.

Run: .venv/bin/python scripts/dfs_certificate_crosscheck.py  (about 2 minutes)
"""
import itertools
import numpy as np
from evoalgo.problem_definitions import DynamicDFS

P = DynamicDFS()

def dfs_runs(g, n):
    out = set()
    # Recursive DFS that branches on every choice of the next unvisited neighbour.
    def go(parent, disc, fin, t, path):
        if not path:
            out.add((tuple(sorted(parent.items())), tuple(sorted(disc.items())), tuple(sorted(fin.items()))))
            return
        u = path[-1]
        nxt = [v for v in range(n) if g[u][v] and v not in disc]
        if not nxt:
            fin2 = dict(fin); fin2[u] = t
            go(parent, disc, fin2, t + 1, path[:-1])
            return
        for v in nxt:
            p2 = dict(parent); p2[v] = u
            d2 = dict(disc); d2[v] = t
            go(p2, d2, fin, t + 1, path + [v])
    go({0: None}, {0: 0}, {}, 1, [0])
    return out

def state_of(cert, n):
    par, disc, fin = (dict(x) for x in cert)
    return {"parent": [par.get(v) for v in range(n)],
            "discover": [disc.get(v, -1) for v in range(n)],
            "finish": [fin.get(v, -1) for v in range(n)]}

total = wrong = 0
for n in range(1, 5):
    pairs = [(u, v) for u in range(n) for v in range(n) if u != v]
    for bits in itertools.product((0, 1), repeat=len(pairs)):
        g = [[0] * n for _ in range(n)]
        for (u, v), b in zip(pairs, bits):
            g[u][v] = b
        G = np.array(g)
        valid = dfs_runs(g, n)
        cands = set(valid)
        for cert in valid:
            par, disc, fin = (dict(x) for x in cert)
            reach = sorted(disc)
            for v in reach:
                if v == 0:
                    continue
                for q in [None] + [w for w in reach if w != v]:
                    if q != par[v]:
                        p2 = dict(par); p2[v] = q
                        cands.add((tuple(sorted(p2.items())), cert[1], cert[2]))
            times = [("d", v) for v in reach] + [("f", v) for v in reach]
            for (k1, a), (k2, b) in itertools.combinations(times, 2):
                d2, f2 = dict(disc), dict(fin)
                x = d2[a] if k1 == "d" else f2[a]
                y = d2[b] if k2 == "d" else f2[b]
                if x == y:
                    continue
                if k1 == "d": d2[a] = y
                else: f2[a] = y
                if k2 == "d": d2[b] = x
                else: f2[b] = x
                cands.add((cert[0], tuple(sorted(d2.items())), tuple(sorted(f2.items()))))
        for c in cands:
            total += 1
            if P.check_invariant(state_of(c, n), G, 0) != (c in valid):
                wrong += 1
print(f"certificates checked: {total}, wrong verdicts: {wrong}")
raise SystemExit(1 if wrong else 0)
