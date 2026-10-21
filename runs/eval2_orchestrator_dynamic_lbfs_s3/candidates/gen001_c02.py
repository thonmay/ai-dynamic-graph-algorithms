"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, check whether the
old ordering is still a valid LexBFS ordering via the (LB) 4-point property.
If it is, return the state unchanged (O(n^3) check, no recompute).
If not, fall back to a full O(n^2) partition-refinement LexBFS recompute.

The (LB) property (Corneil & Krueger): for all positions a < b < c in the
ordering with ac in E and ab not in E, there exists d < a with db in E and
dc not in E.  An ordering is a valid LexBFS ordering iff it satisfies (LB).
"""


def _check_lb(order, adj):
    """Check the (LB) 4-point property. Return True if valid."""
    n = len(order)
    # nbrs[v] = set of neighbors of v
    nbrs = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                nbrs[u].add(v)
                nbrs[v].add(u)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if va in nbrs[vb]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > b with ac in E
            for c in range(b + 1, n):
                vc = order[c]
                if va not in nbrs[vc]:
                    continue  # ac not in E
                # Need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = order[d]
                    if vb in nbrs[vd] and vc not in nbrs[vd]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _lexbfs_full(adj):
    """Full O(n^2) LexBFS via partition refinement. Returns ordering list."""
    n = len(adj)
    if n == 0:
        return []
    # buckets: list of lists of vertices with the same label so far
    buckets = [[v for v in range(n)]]
    order = []

    while buckets:
        # pick first vertex of first bucket
        v = buckets[0][0]
        buckets[0].pop(0)
        if not buckets[0]:
            buckets.pop(0)
        order.append(v)
        # refine all remaining buckets by adjacency to v
        new_buckets = []
        for b in buckets:
            b1 = [x for x in b if adj[v][x]]
            b0 = [x for x in b if not adj[v][x]]
            if b1:
                new_buckets.append(b1)
            if b0:
                new_buckets.append(b0)
        buckets = new_buckets

    return order


def init(graph):
    n = len(graph)
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _check_lb(order, graph):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph)}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _check_lb(order, graph):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph)}
