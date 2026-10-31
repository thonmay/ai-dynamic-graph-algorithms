# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Random-update check of the Yang et al. dynamic DFS reference beyond the bound.

For every graph size n = 6..30 and eight edge densities, build seeded random
digraphs, apply random edge insertions and deletions to the reference
(selftest/references.py, YANG_DFS_CODE), and check the DFS certificate of the
maintained state with the verifier's own checker after every update.

Run: .venv/bin/python scripts/yang_random_check.py  (about 10 to 20 minutes)
"""
import random
import sys

import numpy as np

from evoalgo.problem_definitions import DynamicDFS
from evoalgo.selftest.references import YANG_DFS_CODE

GRAPHS_PER_CELL = 3
UPDATES_PER_GRAPH = 2400
DENSITIES = (0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7)


def main() -> int:
    ns: dict = {}
    exec(compile(YANG_DFS_CODE, "<yang>", "exec"), ns)
    init, ins, dele = ns["init"], ns["insert_edge"], ns["delete_edge"]
    checker = DynamicDFS()
    rng = random.Random(20261026)
    updates = violations = 0
    for n in range(6, 31):
        for p in DENSITIES:
            for _ in range(GRAPHS_PER_CELL):
                g = [[1 if u != v and rng.random() < p else 0 for v in range(n)] for u in range(n)]
                state = init([row[:] for row in g])
                for _ in range(UPDATES_PER_GRAPH):
                    u, v = rng.sample(range(n), 2)
                    if g[u][v]:
                        g[u][v] = 0
                        state = dele([row[:] for row in g], (u, v), state)
                    else:
                        g[u][v] = 1
                        state = ins([row[:] for row in g], (u, v), state)
                    updates += 1
                    if not checker.check_invariant(state, np.array(g), 0):
                        violations += 1
        print(f"n={n}: {updates} updates so far, {violations} violations", flush=True)
    print(f"total: {updates} updates on n = 6..30, {len(DENSITIES)} densities, "
          f"{violations} invariant violations")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
