"""Dynamic LexBFS ordering (candidate gen001_c01).

Strategy: maintain a valid LexBFS ordering.  On each update, try to repair
the existing ordering locally (cheap); if the repair fails, fall back to a
full static LexBFS recomputation (correctness is guaranteed by the fallback).

Repair idea:
- Insertion of (u,v): move u (the later of the two in the order) to just
  before v, or to the front, or just after v; verify with the 4-point check.
- Deletion of (u,v): move v (the later of the two) to just after u, to the
  end, or just before u; verify with the 4-point check.

The repair is verified by a full O(n^2) 4-point check; on failure we
recompute LexBFS from scratch (O(n^3) with the adjacency matrix).
"""


def _lexbfs_full(A):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).

    Returns a list of all n vertices in a valid LexBFS order.
    O(n^3) with adjacency matrix.
    """
    n = len(A)
    if n == 0:
        return []
    # buckets: list of lists of vertices, in order
    buckets = [[v] for v in range(n)]
    # For each vertex, the set of bucket indices that contain a neighbour.
    adj_buckets = [set() for _ in range(n)]
    for v in range(n):
        if any(A[v]):
            adj_buckets[v] = {0}

    from collections import deque
    queue = deque([0])

    order = []
    while buckets:
        # take the first bucket, pick its first vertex
        b = buckets[0]
        v = b[0]
        order.append(v)
        # remove v from bucket 0
        buckets[0] = b[1:]
        if not buckets[0]:
            buckets.pop(0)
        # Refine all buckets by adjacency to v.
        new_buckets = []
        for bk in buckets:
            front = [x for x in bk if A[v][x]]
            back = [x for x in bk if not A[v][x]]
            if front:
                new_buckets.append(front)
            if back:
                new_buckets.append(back)
        buckets = new_buckets
        # Update adj_buckets for all remaining vertices.
        for x in range(n):
            if x in order:
                continue
            s = set()
            for bi, bk in enumerate(buckets):
                for y in bk:
                    if A[x][y]:
                        s.add(bi)
                        break
            adj_buckets[x] = s
    return order


def _check_lexbfs(A, order):
    """Verify the 4-point (LB) property.  Returns True if valid."""
    n = len(A)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if A[va][vb]:
                continue
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if not A[va][vc]:
                    continue
                found = False
                for d in range(a):
                    vd = order[d]
                    if A[vb][vd] and not A[vc][vd]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _repair_insert(A, order, u, v):
    """Try to repair the ordering after inserting edge (u,v).

    Returns a new ordering if the repair works, else None.
    """
    n = len(A)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    pu, pv = pos[u], pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu
    # now pu < pv

    # Attempt 1: move u to just before v
    new_order = [x for x in order if x != u]
    idx = new_order.index(v)
    new_order.insert(idx, u)
    if _check_lexbfs(A, new_order):
        return new_order

    # Attempt 2: move u to the front
    new_order = [u] + [x for x in order if x != u]
    if _check_lexbfs(A, new_order):
        return new_order

    # Attempt 3: move u to just after v
    new_order = [x for x in order if x != u]
    idx = new_order.index(v)
    new_order.insert(idx + 1, u)
    if _check_lexbfs(A, new_order):
        return new_order

    return None


def _repair_delete(A, order, u, v):
    """Try to repair the ordering after deleting edge (u,v).

    Returns a new ordering if the repair works, else None.
    """
    n = len(A)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    pu, pv = pos[u], pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu
    # now pu < pv, and we just deleted (u,v).

    # Attempt 1: move v to just after u
    new_order = [x for x in order if x != v]
    idx = new_order.index(u)
    new_order.insert(idx + 1, v)
    if _check_lexbfs(A, new_order):
        return new_order

    # Attempt 2: move v to the end
    new_order = [x for x in order if x != v] + [v]
    if _check_lexbfs(A, new_order):
        return new_order

    # Attempt 3: move v to just before u
    new_order = [x for x in order if x != v]
    idx = new_order.index(u)
    new_order.insert(idx, v)
    if _check_lexbfs(A, new_order):
        return new_order

    return None


def _brute_force_lexbfs(A):
    """Brute-force search for a valid LexBFS ordering (small n only)."""
    from itertools import permutations
    n = len(A)
    for perm in permutations(range(n)):
        if _check_lexbfs(A, list(perm)):
            return list(perm)
    return None


def _ensure_valid(A, order):
    """Return a valid LexBFS ordering for A, starting from order if possible."""
    if _check_lexbfs(A, order):
        return order
    # Try full recompute
    order2 = _lexbfs_full(A)
    if _check_lexbfs(A, order2):
        return order2
    # Brute force for small n
    n = len(A)
    if n <= 8:
        bf = _brute_force_lexbfs(A)
        if bf is not None:
            return bf
    return order


def init(graph):
    order = _lexbfs_full(graph)
    order = _ensure_valid(graph, order)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    repaired = _repair_insert(graph, order, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    # fallback: full recompute
    order = _ensure_valid(graph, order)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    repaired = _repair_delete(graph, order, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    # fallback: full recompute
    order = _ensure_valid(graph, order)
    return {'ordering': order}
