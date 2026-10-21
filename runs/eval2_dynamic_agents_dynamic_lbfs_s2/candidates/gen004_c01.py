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

    Bitset implementation: for each position a, N(a) is the set of
    vertices adjacent to order[a]. For each b > a with order[b] not in
    N(a), the set of c > b with order[c] in N(a) must be covered by the
    union, over d < a, of (N(d) \\ N(a)).
    """
    n = len(order)
    if n == 0:
        return True
    N = [0] * n
    for i in range(n):
        vi = order[i]
        row = A[vi]
        mask = 0
        for j in range(n):
            if row[order[j]]:
                mask |= 1 << j
        N[i] = mask
    for a in range(n):
        Na = N[a]
        # Union over d < a of N(d) \\ N(a).
        cover = 0
        for d in range(a):
            cover |= N[d] & ~Na
        # Candidates b: positions > a not adjacent to a.
        bmask = ((1 << n) - 1) & ~((1 << (a + 1)) - 1) & ~Na
        while bmask:
            lb = bmask & -bmask
            b = lb.bit_length() - 1
            bmask ^= lb
            # c positions: > b and adjacent to a.
            cmask = Na & ~((1 << (b + 1)) - 1)
            if cmask & ~cover:
                return False
    return True


def _local_repair(A, order, affected):
    """Try to repair the ordering by reinserting affected vertices.

    Returns a new ordering if valid, else None.
    """
    n = len(A)
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


def _local_repair2(A, order, affected):
    """Repair by reinserting affected vertices, one at a time, in the
    order they appear in the old ordering.

    For each affected vertex v (in old-order position), remove it from
    the current ordering and reinsert it at the first position where the
    (LB) certificate holds. If no position works, return None.
    """
    n = len(A)
    if not affected:
        return order

    aff = [v for v in order if v in affected]
    cur = list(order)
    for v in aff:
        if v not in cur:
            continue
        cur.remove(v)
        placed = False
        for pos in range(len(cur) + 1):
            trial = cur[:pos] + [v] + cur[pos:]
            if _check_lb(A, trial):
                cur = trial
                placed = True
                break
        if not placed:
            return None
    return cur


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
        new_order = _local_repair2(A, order, affected)
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
        new_order = _local_repair2(A, order, affected)
    if new_order is None:
        new_order = _lexbfs_full(A)
    return {'ordering': new_order, 'A': A}
