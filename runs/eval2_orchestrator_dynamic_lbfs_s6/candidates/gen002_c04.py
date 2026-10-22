"""Dynamic LexBFS ordering (candidate gen002_c04).

Maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n^2) with the adjacency matrix.
  * update: (1) if the old ordering is still valid (checked with the (LB)
    4-point certificate in O(n^2) using bitsets), keep it; (2) otherwise try
    a cheap local repair (move one endpoint of the flipped edge to a
    position guided by the certificate), certifying each candidate with the
    same O(n^2) check; (3) otherwise fall back to a full recompute.

The (LB) 4-point property (Corneil-Krueger): for all positions a < b < c
with ac in E and ab not in E, there exists d < a with db in E and dc not
in E.  It characterizes exactly the LexBFS orderings, so the certificate
check is a sound and complete validity test.
"""


# ---------------------------------------------------------------------------
# static LexBFS (partition refinement)
# ---------------------------------------------------------------------------

def _lexbfs_full(A):
    """Static partition-refinement LexBFS on adjacency matrix A. O(n^2).

    Bucket queue in (label, insertion order) order; the first vertex of
    the first non-empty bucket is output, and every remaining bucket is
    split by adjacency to it (adjacent part first).
    """
    n = len(A)
    if n == 0:
        return []
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
                new_buckets.append([k | frozenset((u,)), adj])
            if non:
                new_buckets.append([k, non])
        buckets = new_buckets
    return order


def _lexbfs_full2(A):
    """Alternative static LexBFS: label-based selection.

    labels[v] = tuple of already-selected neighbors of v, in selection
    order (the lexicographic key).  Repeatedly select the unselected
    vertex with the lexicographically smallest label (tie-break: smallest
    id), append it to the order, and append it to the labels of its
    unselected neighbors.  O(n^3) worst case but simple and correct.
    """
    n = len(A)
    if n == 0:
        return []
    labels = [() for _ in range(n)]
    unselected = list(range(n))
    order = []
    for _ in range(n):
        best = None
        best_label = None
        for v in unselected:
            lab = labels[v]
            if best is None or lab < best_label or (lab == best_label and v < best):
                best = v
                best_label = lab
        order.append(best)
        unselected.remove(best)
        for u in unselected:
            if A[best][u]:
                labels[u] = labels[u] + (best,)
    return order


# ---------------------------------------------------------------------------
# (LB) 4-point certificate, bitset version
# ---------------------------------------------------------------------------

def _is_valid_lexbfs(A, order):
    """Check the (LB) 4-point property in O(n^2) bit operations.

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E.

    Iterating c outermost: for each b < c with bc not in E, let
    A = {a < b : ac in E}.  For every a in A we need
        (N(b) & [0, a)) & ~N(c) != 0
    which is a constant-time bit operation per (a, b, c) triple.
    """
    n = len(order)
    nbr = [0] * n  # nbr[i] = bitmask of positions adjacent to position i
    for i in range(n):
        u = order[i]
        bits = 0
        row = A[u]
        for j in range(n):
            if row[order[j]]:
                bits |= 1 << j
        nbr[i] = bits
    full = (1 << n) - 1
    for c in range(n):
        not_c = full ^ nbr[c]
        for b in range(c):
            if (nbr[b] >> c) & 1:
                continue  # bc in E: no constraint
            Aset = nbr[c] & ((1 << b) - 1)
            if not Aset:
                continue
            nb = nbr[b]
            bits = Aset
            while bits:
                low = bits & (-bits)  # 1 << a
                if ((nb & (low - 1)) & not_c) == 0:
                    return False
                bits ^= low
    return True


# ---------------------------------------------------------------------------
# local repair
# ---------------------------------------------------------------------------

def _try_local_repair(A, order, edge):
    """Try to repair the ordering after a single edge update.

    For each endpoint mv of the flipped edge (u, v), repeatedly move mv to
    just before the earliest vertex b (before mv's current position) that
    is not adjacent to mv; stop when no such b exists.  Certify the result
    with the (LB) check.  Return the first certified ordering, else None.
    """
    n = len(order)
    u, v = edge
    for mv in (u, v):
        cur = list(order)
        for _ in range(n):
            pos = [0] * n
            for i, x in enumerate(cur):
                pos[x] = i
            target = None
            for i in range(pos[mv]):
                if not A[cur[i]][mv]:
                    target = i
                    break
            if target is None:
                break
            cur = [x for x in cur if x != mv]
            cur.insert(target, mv)
        if _is_valid_lexbfs(A, cur):
            return cur
    # Second pass: try moving each endpoint to just after the other
    # endpoint (useful after edge deletions, where the endpoint may need
    # to move later in the order).
    for mv in (u, v):
        other = v if mv == u else u
        cur = list(order)
        pos = [0] * n
        for i, x in enumerate(cur):
            pos[x] = i
        cur = [x for x in cur if x != mv]
        cur.insert(pos[other] + 1, mv)
        if _is_valid_lexbfs(A, cur):
            return cur
    # Third pass: try moving each endpoint to the front of the order.
    for mv in (u, v):
        cur = list(order)
        cur.remove(mv)
        cur.insert(0, mv)
        if _is_valid_lexbfs(A, cur):
            return cur
    # Fourth pass: try every single-move position for each endpoint.
    for mv in (u, v):
        base = [x for x in order if x != mv]
        for t in range(n):
            cur = list(base)
            cur.insert(t, mv)
            if _is_valid_lexbfs(A, cur):
                return cur
    return None


# ---------------------------------------------------------------------------
# public interface
# ---------------------------------------------------------------------------

def init(graph):
    order = _lexbfs_full(graph)
    if not _is_valid_lexbfs(graph, order):
        order = _lexbfs_full2(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    fixed = _try_local_repair(graph, order, edge)
    if fixed is not None:
        return {'ordering': fixed}
    return {'ordering': _lexbfs_full(graph)}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    fixed = _try_local_repair(graph, order, edge)
    if fixed is not None:
        return {'ordering': fixed}
    return {'ordering': _lexbfs_full(graph)}
