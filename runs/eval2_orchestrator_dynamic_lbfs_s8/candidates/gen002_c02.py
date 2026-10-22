"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each edge update:
  1. If the current ordering is still valid (cheap check), keep it.
  2. Try a cheap local repair: move one of the two affected vertices to a
     better position, or swap two nearby vertices.
  3. Fall back to a full O(n^2) LexBFS recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lb_valid(order, adj):
    """Check the (LB) 4-point property of Corneil and Krueger.

    For all a < b < c with ac in E and ab not in E, there exists
    d < a with db in E and dc not in E.
    O(n^4) worst case, early exit.
    """
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb]:
                continue
            # ab not in E; check if there exists c > b with ac in E
            for c in range(b + 1, n):
                vc = order[c]
                if not adj[va][vc]:
                    continue
                # ac in E, ab not in E, a < b < c: need d < a with d~vb and not d~vc
                ok = False
                for d in range(a):
                    vd = order[d]
                    if adj[vd][vb] and not adj[vd][vc]:
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


def _try_move(order, adj, cv, candidates):
    """Try moving vertex cv to one of the candidate positions.

    Returns a new order if valid, else None.
    """
    n = len(order)
    old_pos = order.index(cv)
    for new_pos in sorted(candidates):
        if new_pos < 0 or new_pos >= n or new_pos == old_pos:
            continue
        new_order = order[:old_pos] + order[old_pos + 1:]
        new_order.insert(new_pos, cv)
        if _lb_valid(new_order, adj):
            return new_order
    return None


def _try_local_repair(order, adj, u, v):
    """Try to fix the ordering by moving or swapping affected vertices.

    Returns a new order if valid, else None.
    """
    n = len(order)
    if n == 0:
        return order

    # For each affected vertex, try moving it near its neighbors.
    for cv in (u, v):
        if cv not in order:
            continue
        old_pos = order.index(cv)
        candidates = set()
        candidates.add(old_pos)
        for i, w in enumerate(order):
            if w == cv:
                continue
            if adj[cv][w]:
                candidates.add(i + 1)  # after w
                candidates.add(i)  # before w
        candidates.add(0)
        candidates.add(n - 1)
        result = _try_move(order, adj, cv, candidates)
        if result is not None:
            return result

    # Try swapping two nearby vertices (within a small window).
    pos_u = order.index(u) if u in order else -1
    pos_v = order.index(v) if v in order else -1
    window = 3
    for i in range(n):
        for j in range(i + 1, min(i + window, n)):
            if i == pos_u or i == pos_v or j == pos_u or j == pos_v:
                continue
            new_order = order[:]
            new_order[i], new_order[j] = new_order[j], new_order[i]
            if _lb_valid(new_order, adj):
                return new_order

    return None


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']

    # 1. If the current ordering is still valid, keep it.
    if _lb_valid(order, graph):
        return {'ordering': order}

    # 2. Try local repair
    repaired = _try_local_repair(order, graph, u, v)
    if repaired is not None:
        return {'ordering': repaired}

    # 3. Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']

    # 1. If the current ordering is still valid, keep it.
    if _lb_valid(order, graph):
        return {'ordering': order}

    # 2. Try local repair
    repaired = _try_local_repair(order, graph, u, v)
    if repaired is not None:
        return {'ordering': repaired}

    # 3. Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order}
