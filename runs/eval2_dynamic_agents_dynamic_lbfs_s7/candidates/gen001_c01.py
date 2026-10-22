"""Dynamic LexBFS ordering.

Baseline candidate: after each update, recompute a static LexBFS
ordering using the partition-refinement algorithm of Habib, McConnell,
Paul and Viennot. The previous ordering is used as a hint for the
start vertex and for tie-breaking, which keeps the ordering stable
across small updates.

State: dict with 'ordering' (list of all n vertices, a valid LexBFS
ordering) and 'n'.
"""


def _lexbfs(graph, n, start, rank):
    """Static LexBFS via partition refinement.

    Buckets are kept as lists (not sets) so that refinement is
    deterministic and tie-breaking by (rank, id) is well-defined.
    """
    if n == 0:
        return []

    # buckets: list of lists of unprocessed vertices, in queue order
    buckets = [[v for v in range(n) if v != start]]

    order = [start]
    processed = [False] * n
    processed[start] = True

    for _ in range(n - 1):
        # pick next vertex: first non-empty bucket, min by (rank, id)
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = min(buckets[bi], key=lambda x: (rank[x], x))
        buckets[bi].remove(v)
        order.append(v)
        processed[v] = True

        # refine all buckets by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                new_buckets.append(b)
                continue
            nb = []
            nb2 = []
            for x in b:
                if graph[x][v]:
                    nb.append(x)
                else:
                    nb2.append(x)
            if nb and nb2:
                new_buckets.append(nb)
                new_buckets.append(nb2)
            else:
                new_buckets.append(b)
        buckets = new_buckets

    return order


def _recompute(graph, state):
    n = state['n']
    hint = state['ordering']
    if not hint:
        start = 0
        rank = [i for i in range(n)]
    else:
        start = hint[0]
        rank = [0] * n
        for i, v in enumerate(hint):
            rank[v] = i
    order = _lexbfs(graph, n, start, rank)
    return {'ordering': order, 'n': n}


def init(graph):
    n = len(graph)
    order = _lexbfs(graph, n, 0, [i for i in range(n)])
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    return _recompute(graph, state)


def delete_edge(graph, edge, state):
    return _recompute(graph, state)
