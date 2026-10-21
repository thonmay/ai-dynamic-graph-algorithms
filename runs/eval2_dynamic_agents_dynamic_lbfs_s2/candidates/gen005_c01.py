"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first check
whether the old ordering is still valid (cheap, O(n^3) worst case but
usually fast); if not, try a local repair (reinsert affected vertices
into the base ordering); if the repair fails the (LB) 4-point
certificate, fall back to a full static LexBFS recomputation.
"""


def _lexbfs_full(A):
    """Static LexBFS via label refinement. O(n^3) worst case.

    Each vertex gets a label (tuple of 0/1) built by processing vertices
    in order. At each step, pick the unprocessed vertex with the
    lexicographically largest label (ties broken by vertex id).
    """
    n = len(A)
    if n == 0:
        return []
    unprocessed = set(range(n))
    labels = {v: [] for v in range(n)}
    order = []

    while unprocessed:
        best = min(unprocessed, key=lambda v: ([-x for x in labels[v]], v))
        order.append(best)
        unprocessed.remove(best)
        for u in unprocessed:
            labels[u].append(1 if A[best][u] else 0)

    return order


def _check_lb(A, order):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Vectorized with bitmasks: for each a, the set of d < a that are
    adjacent to b but not to c must be non-empty for every such triple.
    """
    n = len(order)
    if n == 0:
        return True
    adj = [0] * n
    for v in range(n):
        row = A[v]
        m = 0
        for u in range(n):
            if row[u]:
                m |= 1 << u
        adj[v] = m
    prefix = 0
    for a in range(n):
        va = order[a]
        ma = adj[va]
        for b in range(a + 1, n):
            vb = order[b]
            if (ma >> vb) & 1:
                continue
            mb = adj[vb]
            for c in range(b + 1, n):
                vc = order[c]
                if not ((ma >> vc) & 1):
                    continue
                # Need some d with pos[d] < a, db in E, dc not in E.
                if (mb & ~adj[vc] & prefix) == 0:
                    return False
        prefix |= 1 << va
    return True


def _local_repair(A, order, affected):
    """Try to repair the ordering by reinserting affected vertices.

    Returns a new ordering if valid, else None.
    """
    if not affected:
        return order

    base = [v for v in order if v not in affected]
    aff = sorted(affected)

    if len(aff) > 6:
        return None

    from itertools import permutations

    for perm in permutations(aff):
        new_order = list(base)
        ok = True
        for v in perm:
            placed = False
            for pos in range(len(new_order) + 1):
                trial = new_order[:pos] + [v] + new_order[pos:]
                if _check_lb(A, trial):
                    new_order = trial
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if ok and _check_lb(A, new_order):
            return new_order

    return None





def init(graph):
    A = [list(row) for row in graph]
    order = _lexbfs_full(A)
    return {'ordering': order, 'A': A}


def insert_edge(graph, edge, state):
    A = [list(row) for row in graph]
    u, v = edge

    order = state['ordering']
    # The old ordering may still be valid after an insertion.
    if _check_lb(A, order):
        return {'ordering': order, 'A': A}

    affected = {u, v}
    for x in range(len(A)):
        if A[u][x] or A[v][x]:
            affected.add(x)

    new_order = _local_repair(A, order, affected)
    if new_order is None:
        new_order = _lexbfs_full(A)
    return {'ordering': new_order, 'A': A}


def delete_edge(graph, edge, state):
    A = [list(row) for row in graph]
    u, v = edge

    order = state['ordering']
    # The old ordering may still be valid after a deletion.
    if _check_lb(A, order):
        return {'ordering': order, 'A': A}

    affected = {u, v}
    for x in range(len(A)):
        if A[u][x] or A[v][x]:
            affected.add(x)

    new_order = _local_repair(A, order, affected)
    if new_order is None:
        new_order = _lexbfs_full(A)
    return {'ordering': new_order, 'A': A}
