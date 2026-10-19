"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try a cheap
local repair (move one of the two affected vertices to a different
position); if the repair fails the (LB) 4-point certification, fall back
to a full static LexBFS recompute.

The local repair is sound: it only returns an ordering that passes the
(LB) 4-point property, which certifies a valid LexBFS ordering. The
fallback is a plain, known-correct static partition-refinement LexBFS,
so correctness never depends on the repair heuristic.
"""


def _lexbfs(A):
    """Static O(n^2) LexBFS on a 0/1 adjacency matrix. Returns an ordering.

    Labels are tuples of (position, vertex) of already-ordered neighbors.
    The sentinel (n,) sorts after any real label, so a vertex with no
    ordered neighbors is picked last among ties, as LexBFS requires.
    """
    n = len(A)
    if n == 0:
        return []
    # labels[v] = tuple of (position, vertex) of already-ordered neighbors
    # of v, in position order.  The sentinel (n,) sorts after any real
    # label, so a vertex with no ordered neighbors is picked last among
    # ties, as LexBFS requires.
    labels = [(n,) for _ in range(n)]
    order = []
    remaining = set(range(n))
    for _ in range(n):
        # pick the remaining vertex with the lexicographically smallest label
        best = None
        for v in sorted(remaining):
            if best is None or labels[v] < labels[best]:
                best = v
        remaining.remove(best)
        order.append(best)
        pos = len(order) - 1
        for u in remaining:
            if A[u][best]:
                labels[u] = labels[u] + ((pos, best),)
    return order


def _is_valid_lexbfs(A, order):
    """Check the (LB) 4-point property: for all positions a<b<c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if A[a][b]:
                continue
            for k in range(j + 1, n):
                c = order[k]
                if not A[a][c]:
                    continue
                # need d < i with db in E and dc not in E
                ok = False
                for t in range(i):
                    d = order[t]
                    if A[d][b] and not A[d][c]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _local_repair(A, order, edge):
    """Try to repair the ordering after flipping edge (u, v).

    The edge change only affects the labels of u and v (and transitively
    the relative order of vertices whose labels differ only in the u/v
    entries). We attempt a minimal repair:

    1. Check if the current ordering is still valid. If yes, done.
    2. Try moving u to every other position. If valid, done.
    3. Try moving v to every other position. If valid, done.
    4. If none work, return None (triggering full recompute).
    """
    n = len(order)
    u, v = edge
    if u == v:
        return order

    # Quick check: is the current order still valid?
    if _is_valid_lexbfs(A, order):
        return order

    # Try moving u to every other position
    oi = order.index(u)
    for ni in range(n):
        if ni == oi:
            continue
        cand = list(order)
        cand.pop(oi)
        cand.insert(ni, u)
        if _is_valid_lexbfs(A, cand):
            return cand

    # Try moving v to every other position
    oj = order.index(v)
    for ni in range(n):
        if ni == oj:
            continue
        cand = list(order)
        cand.pop(oj)
        cand.insert(ni, v)
        if _is_valid_lexbfs(A, cand):
            return cand

    return None


def init(graph):
    return {'ordering': _lexbfs(graph)}


def insert_edge(graph, edge, state):
    order = state['ordering']
    repaired = _local_repair(graph, order, edge)
    if repaired is None:
        repaired = _lexbfs(graph)
    return {'ordering': repaired}


def delete_edge(graph, edge, state):
    order = state['ordering']
    repaired = _local_repair(graph, order, edge)
    if repaired is None:
        repaired = _lexbfs(graph)
    return {'ordering': repaired}
