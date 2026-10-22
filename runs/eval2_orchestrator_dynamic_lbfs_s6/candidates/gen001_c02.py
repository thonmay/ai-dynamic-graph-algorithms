"""Dynamic LexBFS ordering.

Maintain a valid LexBFS ordering. On each edge update, try a cheap local
repair (move the endpoint v of the flipped edge (u,v) to just before the
earliest vertex b that is not adjacent to v and appears before u in the
order). Then verify the (LB) 4-point property in O(n^2); if it fails,
recompute LexBFS from scratch (O(n^2) with the adjacency matrix).

Correctness is guaranteed by the verification + fallback.
"""


def _lexbfs_full(A):
    """Static partition-refinement LexBFS on adjacency matrix A. O(n^2)."""
    n = len(A)
    # buckets: list of [key, list]; key = frozenset of earlier-neighbors.
    buckets = [[frozenset(), list(range(n))]]
    order = []
    for _ in range(n):
        bi = 0
        while not buckets[bi][1]:
            bi += 1
        key, lst = buckets[bi]
        u = lst.pop(0)
        order.append(u)
        new_buckets = []
        for k, L in buckets:
            if not L:
                continue
            adj = [x for x in L if A[u][x]]
            non = [x for x in L if not A[u][x]]
            if adj:
                new_buckets.append([k | frozenset([u]), adj])
            if non:
                new_buckets.append([k, non])
        buckets = new_buckets
    return order


def _is_valid_lexbfs(A, order):
    """Check the (LB) 4-point property in O(n^2).

    For all positions a < b < c with A[a][c] and not A[a][b], there must
    exist d < a with A[d][b] and not A[d][c].
    """
    n = len(A)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if A[va][vb]:
                continue
            # W = {d < a : A[d][vb]}
            W = [order[d] for d in range(a) if A[order[d]][vb]]
            if not W:
                # then no c > b may satisfy A[va][c]
                for c in range(b + 1, n):
                    if A[va][order[c]]:
                        return False
                continue
            Wset = set(W)
            for c in range(b + 1, n):
                vc = order[c]
                if not A[va][vc]:
                    continue
                ok = False
                for d in Wset:
                    if not A[d][vc]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _try_both_endpoints(A, order, edge, inserted, max_moves=8):
    """Try local repair moving u, then moving v; return the first that
    passes the (LB) check, else None."""
    u, v = edge
    for mv in (u, v):
        other = v if mv == u else u
        cur = list(order)
        for _ in range(max_moves):
            pos = [0] * len(A)
            for i, x in enumerate(cur):
                pos[x] = i
            target = None
            for i in range(pos[other]):
                b = cur[i]
                if not A[b][mv]:
                    target = i
                    break
            if target is None:
                break
            cur = [x for x in cur if x != mv]
            cur.insert(target, mv)
        if _is_valid_lexbfs(A, cur):
            return cur
    return None


def init(graph):
    return {'ordering': _lexbfs_full(graph)}


def insert_edge(graph, edge, state):
    fixed = _try_both_endpoints(graph, state['ordering'], edge, True)
    if fixed is not None:
        return {'ordering': fixed}
    return {'ordering': _lexbfs_full(graph)}


def delete_edge(graph, edge, state):
    fixed = _try_both_endpoints(graph, state['ordering'], edge, False)
    if fixed is not None:
        return {'ordering': fixed}
    return {'ordering': _lexbfs_full(graph)}
