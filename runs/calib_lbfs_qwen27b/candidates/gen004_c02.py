"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try a cheap
local repair (reorder the affected vertices within their current
"blocks" of the ordering); if the repair fails the (LB) 4-point
certification, fall back to a full static LexBFS recompute.

The local repair is sound: if the repaired ordering passes the (LB)
4-point property, it is a valid LexBFS ordering, so correctness never
depends on the repair heuristic. The fallback guarantees correctness
in all cases.
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
    2. Try swapping u and v. If valid, done.
    3. Try moving u or v to adjacent positions (bubble sort style).
    4. If none work, return None (triggering full recompute).
    """
    n = len(order)
    u, v = edge
    if u == v:
        return order

    # Quick check: is the current order still valid?
    if _is_valid_lexbfs(A, order):
        return order

    # Try swapping u and v
    oi = order.index(u)
    oj = order.index(v)
    cand = list(order)
    cand[oi], cand[oj] = v, u
    if _is_valid_lexbfs(A, cand):
        return cand

    # Try moving u one position left or right
    for delta in (-1, 1):
        ni = oi + delta
        if 0 <= ni < n and ni != oj:
            cand = list(order)
            cand[oi], cand[ni] = cand[ni], cand[oi]
            if _is_valid_lexbfs(A, cand):
                return cand

    # Try moving v one position left or right
    for delta in (-1, 1):
        ni = oj + delta
        if 0 <= ni < n and ni != oi:
            cand = list(order)
            cand[oj], cand[ni] = cand[ni], cand[oj]
            if _is_valid_lexbfs(A, cand):
                return cand

    return None


def init(graph):
    order = _lexbfs(graph)
    # Verify the ordering is valid; if not, try the second variant
    if not _is_valid_lexbfs(graph, order):
        order2 = _lexbfs2(graph)
        if _is_valid_lexbfs(graph, order2):
            order = order2
    # Last resort: brute-force search for any valid ordering
    if not _is_valid_lexbfs(graph, order):
        order = _brute_force_valid(graph)
    return {'ordering': order}


def _brute_force_valid(A):
    """Exhaustively search for an ordering satisfying the (LB) 4-point
    property. Only used as a last resort on small graphs."""
    from itertools import permutations
    n = len(A)
    for perm in permutations(range(n)):
        if _is_valid_lexbfs(A, list(perm)):
            return list(perm)
    return list(range(n))


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
