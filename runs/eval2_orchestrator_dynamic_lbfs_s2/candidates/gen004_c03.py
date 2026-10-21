"""Dynamic LexBFS ordering (candidate gen004_c03, repaired).

Strategy: maintain a valid LexBFS ordering in the state. After each edge
update, recompute a fresh LexBFS ordering with the static
partition-refinement algorithm (Habib-McConnell-Paul-Viennot style).

The previous version kept the old ordering when a local 4-point check
passed, but that check was weaker than the verifier's (it skipped triples
with ab in E), so it could return orderings the verifier rejected.  The
repair drops the fast path entirely: every update recomputes, which is
correct for all graphs and updates.
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

        # refine: for each bucket, split off vertices adjacent to v;
        # the adjacent part (label extended with v, lexicographically
        # larger) keeps the bucket's position, the non-adjacent part
        # goes after it
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
                new_buckets.append(nb)
                if rest:
                    new_buckets.append(rest)
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
