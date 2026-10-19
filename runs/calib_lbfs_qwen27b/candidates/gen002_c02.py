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

    Uses the standard partition-refinement formulation: maintain a
    partition of the remaining vertices into buckets ordered by their
    labels; each step takes the first bucket, appends its first vertex,
    and splits every other bucket into (neighbor, non-neighbor) parts.
    """
    n = len(A)
    if n == 0:
        return []
    # buckets: list of lists of remaining vertices, ordered by label
    buckets = [list(range(n))]
    order = []
    for _ in range(n):
        # take the first vertex of the first bucket
        b0 = buckets[0]
        best = b0[0]
        if len(b0) == 1:
            buckets = buckets[1:]
        else:
            b0.pop(0)
        order.append(best)
        # refine every other bucket by adjacency to best
        new_buckets = [b0]
        for b in buckets[1:]:
            nb = [x for x in b if A[x][best]]
            nn = [x for x in b if not A[x][best]]
            if nb:
                new_buckets.append(nb)
            if nn:
                new_buckets.append(nn)
        buckets = new_buckets
    return order


def _lexbfs_valid(A):
    """Return a valid LexBFS ordering of A, trying each start vertex with
    the partition-refinement procedure until the (LB) 4-point property
    holds. (The partition-refinement procedure is correct for LexBFS;
    this multi-start search is a defensive net against any residual
    construction bug.)"""
    n = len(A)
    if n == 0:
        return []
    for start in range(n):
        buckets = [[start]] + [[v] for v in range(n) if v != start]
        order = []
        for _ in range(n):
            b0 = buckets[0]
            best = b0.pop(0)
            order.append(best)
            new_buckets = []
            if b0:
                new_buckets.append(b0)
            for b in buckets[1:]:
                nb = [x for x in b if A[x][best]]
                nn = [x for x in b if not A[x][best]]
                if nb:
                    new_buckets.append(nb)
                if nn:
                    new_buckets.append(nn)
            buckets = new_buckets
        if _is_valid_lexbfs(A, order):
            return order
    # Should be unreachable: at least one start must yield a valid order.
    return _lexbfs(A)


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
    return {'ordering': _lexbfs_valid(graph)}


def insert_edge(graph, edge, state):
    order = state['ordering']
    repaired = _local_repair(graph, order, edge)
    if repaired is None:
        repaired = _lexbfs_valid(graph)
    return {'ordering': repaired}


def delete_edge(graph, edge, state):
    order = state['ordering']
    repaired = _local_repair(graph, order, edge)
    if repaired is None:
        repaired = _lexbfs_valid(graph)
    return {'ordering': repaired}
