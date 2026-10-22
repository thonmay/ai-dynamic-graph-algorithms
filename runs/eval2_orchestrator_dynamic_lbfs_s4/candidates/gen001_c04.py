"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge: if the new edge (u,v) is consistent with the current ordering
  (the earlier vertex's non-neighbor set is a subset of the later vertex's),
  the ordering stays valid; otherwise recompute.
- delete_edge: if the removed edge (u,v) is "witnessed" by the current
  ordering (there exists d < u with d~v and not d~u, where u is the earlier
  endpoint), the ordering stays valid; otherwise recompute.

Both incremental checks are O(n).  The (LB) 4-point property of Corneil and
Krueger certifies validity, and the two lemmas below justify the checks.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement.  Returns the ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets of vertices, in queue order
    buckets = [set(range(n))]
    order = []

    while buckets:
        # pop the first non-empty bucket
        while buckets and not buckets[0]:
            buckets.pop(0)
        if not buckets:
            break
        B = buckets.pop(0)
        for v in sorted(B):
            order.append(v)
            # refine every remaining bucket by adjacency to v
            new_buckets = []
            for C in buckets:
                if not C:
                    continue
                Cn = set()
                Cy = set()
                for w in C:
                    if graph[v][w]:
                        Cy.add(w)
                    else:
                        Cn.add(w)
                if Cn:
                    new_buckets.append(Cn)
                if Cy:
                    new_buckets.append(Cy)
            buckets = new_buckets
    return order


def _recompute(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def _insert_ok(graph, u, v, order):
    """After adding edge (u,v), is `order` still a valid LexBFS?

    Let u be the earlier endpoint in `order`.  The ordering stays valid iff
    N(u) \\ {v}  subset  N(v) \\ {u}, i.e. every non-neighbor of u (other than
    v) is also a non-neighbor of v.  Equivalently: for every w with
    pos(w) < pos(u) and not graph[u][w], we need not graph[v][w].
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    if pos[u] > pos[v]:
        u, v = v, u
    # u is earlier.  For every w before u that is not adjacent to u,
    # w must not be adjacent to v either (otherwise the new edge creates
    # a violation).
    for w in range(n):
        if w == u or w == v:
            continue
        if pos[w] < pos[u] and not graph[u][w] and graph[v][w]:
            return False
    return True


def _delete_ok(graph, u, v, order):
    """After removing edge (u,v), is `order` still a valid LexBFS?

    Let u be the earlier endpoint.  The ordering stays valid iff there is a
    witness d with d < u, d~v and not d~u.  (The removed edge was the only
    thing that could have been needed as a witness for some 4-point
    violation, and the witness condition guarantees none arises.)
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    if pos[u] > pos[v]:
        u, v = v, u
    # u is earlier.  Need d with pos(d) < pos(u), graph[d][v] and not graph[d][u].
    for w in range(n):
        if w == u or w == v:
            continue
        if pos[w] < pos[u] and graph[w][v] and not graph[w][u]:
            return True
    return False


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    if _insert_ok(graph, u, v, order):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    if _delete_ok(graph, u, v, order):
        return state
    return _recompute(graph)
