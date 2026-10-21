"""Dynamic LexBFS ordering (gen003_c03, repaired).

The previous candidate kept the old ordering whenever its local 4-point
check passed, but that check was weaker than the verifier's: it skipped
triples with ab in E, so it could not see violations the verifier flags
(e.g. the triangle after inserting (0,2), where [0,1,2] was kept but the
verifier demanded a witness for (a,b,c)=(0,1,2)).

Repair: drop the keep-old-ordering fast path entirely.  Every update
recomputes a fresh static LexBFS ordering, which is a genuine LexBFS and
therefore satisfies whatever 4-point formulation the verifier enforces.
Correctness first; the O(n+m) cost per update is the safe baseline.
"""


def _lexbfs(graph):
    """Static LexBFS: return a valid ordering of all vertices."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets of vertices with identical label
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket, take its smallest vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        v = min(buckets[bi])
        buckets[bi].discard(v)
        order.append(v)

        # refine: for each bucket, split off vertices adjacent to v
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = set()
            for x in b:
                if graph[v][x]:
                    nb.add(x)
            if nb:
                rest = b - nb
                if rest:
                    new_buckets.append(rest)
                new_buckets.append(nb)
            else:
                new_buckets.append(b)
        buckets = new_buckets

    return order


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = _lexbfs(graph)
    return {'ordering': order}
