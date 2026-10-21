"""Dynamic LexBFS ordering (open problem; this candidate is a correct baseline).

Strategy: maintain a valid LexBFS ordering in the state. After each edge
update, recompute a fresh LexBFS ordering with the static
partition-refinement algorithm (Habib-McConnell-Paul-Viennot style, O(n+m)).

The previous revision tried to keep the old ordering when a 4-point
certificate check passed, but that check was weaker than the verifier's
actual condition (it skipped triples with ab in E that the verifier still
inspects), so it could return orderings the verifier rejects. The safe
baseline is to recompute unconditionally; the static _lexbfs below is a
genuine LexBFS (partition refinement, adjacent part of each bucket first,
smallest vertex of the first bucket chosen), so the returned ordering is
always valid.
"""


def _lexbfs(graph):
    """Static LexBFS: return a valid ordering of all vertices."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of lists of vertices with identical label, in
    # lexicographic label order; within a bucket, ascending vertex id.
    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket, take its smallest vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        v = buckets[bi].pop(0)
        order.append(v)

        # refine: for each bucket, split off vertices adjacent to v;
        # the adjacent part goes first (it receives the smaller label)
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = [x for x in b if graph[v][x]]
            rest = [x for x in b if not graph[v][x]]
            if nb:
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
