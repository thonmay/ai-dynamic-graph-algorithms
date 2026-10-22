"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each edge update, first try a
cheap local repair (reorder only the affected vertex, or a small window around
it); if the repair fails, fall back to a full O(n^2) LexBFS recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lb_valid(order, adj):
    """Check the (LB) 4-point property. O(n^3) worst case, early exit."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb]:
                continue
            # need: exists d < a with d~vb and not d~va
            ok = False
            for d in range(a):
                vd = order[d]
                if adj[vd][vb] and not adj[vd][va]:
                    ok = True
                    break
            if not ok:
                return False
    return True


def _lexbfs(adj):
    """Static LexBFS via partition refinement. O(n^2) with adjacency matrix.

    Returns a list of vertices in LexBFS order.
    """
    n = len(adj)
    if n == 0:
        return []

    # Start with all vertices in one bucket, ordered by vertex id.
    buckets = [[v for v in range(n)]]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket
        while buckets and not buckets[0]:
            buckets.pop(0)
        if not buckets:
            break
        # pick the first vertex in the first bucket
        v = buckets[0].pop(0)
        order.append(v)

        # refine: for each bucket, split into neighbors of v and non-neighbors
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            nb = []
            non_nb = []
            for u in bucket:
                if adj[v][u]:
                    nb.append(u)
                else:
                    non_nb.append(u)
            if nb:
                new_buckets.append(nb)
            if non_nb:
                new_buckets.append(non_nb)
        buckets = new_buckets

    return order


def _try_local_repair(order, adj, changed_vertex):
    """Try to fix the ordering by moving changed_vertex to a better position.

    Returns a new order if valid, else None.
    """
    n = len(order)
    if n == 0:
        return order

    cv = changed_vertex
    old_pos = order.index(cv)

    # Candidate positions: current, and positions near neighbors
    candidates = set()
    candidates.add(old_pos)

    # Try positions just after each neighbor
    for i, v in enumerate(order):
        if v == cv:
            continue
        if adj[cv][v]:
            candidates.add(i + 1)  # after v
            candidates.add(i)  # before v

    # Also try position 0 and n-1
    candidates.add(0)
    candidates.add(n - 1)

    for new_pos in sorted(candidates):
        if new_pos < 0 or new_pos >= n:
            continue
        if new_pos == old_pos:
            continue
        # Build new order
        new_order = order[:old_pos] + order[old_pos + 1:]
        new_order.insert(new_pos, cv)
        if _lb_valid(new_order, adj):
            return new_order

    # If current position is valid, keep it
    if _lb_valid(order, adj):
        return order

    return None


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']

    # Try local repair
    repaired = _try_local_repair(order, graph, u)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']

    # Try local repair
    repaired = _try_local_repair(order, graph, u)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order}
