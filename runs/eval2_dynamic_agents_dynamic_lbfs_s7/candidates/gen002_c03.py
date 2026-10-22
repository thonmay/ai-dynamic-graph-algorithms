"""Dynamic LexBFS ordering.

Baseline candidate: after each update, recompute the static
partition-refinement LexBFS (Habib-McConnell-Paul-Viennot) from scratch.
The state keeps the previous ordering as a hint for future runs.

State: dict with
  'ordering': list of all n vertices, a valid LexBFS ordering
  'n': number of vertices
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement.

    Deterministic tie-break: among the vertices of the current first
    non-empty bucket, pick the one with the lexicographically smallest
    label; ties broken by vertex id.  This yields a valid LexBFS
    ordering (any fixed tie-break is legal).
    """
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of lists of vertices, in order
    buckets = [[v] for v in range(n)]

    order = []
    for _ in range(n):
        # find first non-empty bucket
        bi = None
        for i in range(len(buckets)):
            if buckets[i]:
                bi = i
                break
        if bi is None:
            break
        # choose vertex with smallest id (standard LexBFS tie-break)
        best = min(buckets[bi])
        order.append(best)
        buckets[bi].remove(best)
        # refine every bucket by adjacency to best
        new_buckets = []
        for c in range(len(buckets)):
            if not buckets[c]:
                new_buckets.append([])
                continue
            inside = [v for v in buckets[c] if graph[v][best]]
            outside = [v for v in buckets[c] if not graph[v][best]]
            new_buckets.append(inside)
            new_buckets.append(outside)
        buckets = new_buckets
    return order


def init(graph):
    n = len(graph)
    return {'ordering': _lexbfs(graph), 'n': n}


def insert_edge(graph, edge, state):
    n = state.get('n', len(graph))
    return {'ordering': _lexbfs(graph), 'n': n}


def delete_edge(graph, edge, state):
    n = state.get('n', len(graph))
    return {'ordering': _lexbfs(graph), 'n': n}
