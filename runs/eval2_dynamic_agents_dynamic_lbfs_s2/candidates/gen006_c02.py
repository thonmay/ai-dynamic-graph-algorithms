"""Dynamic LexBFS ordering (gen006_c02).

Strategy: maintain a valid LexBFS ordering. On each update:
  1. If the old ordering is still valid, keep it.
  2. Otherwise try a local repair: reinsert the affected vertices
     (the endpoints plus their common neighbours) into the base
     ordering, choosing the earliest position that keeps the (LB)
     4-point property.
  3. If the repair fails, fall back to a full static LexBFS.

This generation's changes vs the parent:
  * The (LB) certificate check is vectorized with bitmasks: for each
    position a, the witness d < a with db in E and dc not in E exists
    iff (adj[b] & ~adj[c] & prefix) != 0, turning the innermost loop
    into one integer op.
  * The adjacency bitmask table is maintained incrementally in the
    state (one bit flip per update) instead of being rebuilt from the
    matrix on every check.
  * The local repair no longer brute-forces permutations of the
    affected set (which was exponential and capped at 6 vertices).
    Instead it reinserts the affected vertices one by one, each at the
    earliest position that keeps the ordering valid. This is
    polynomial, works for any number of affected vertices, and is
    sound: the final ordering is verified with the full certificate
    before being accepted.
"""


def _lexbfs_full(A):
    """Static LexBFS via label refinement. O(n^3) worst case.

    Each vertex gets a label (tuple of 0/1) built by processing
    vertices in order. At each step, pick the unprocessed vertex with
    the lexicographically largest label (ties broken by vertex id).
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


def _build_adj(A):
    """Build the adjacency bitmask table from a 0/1 matrix."""
    n = len(A)
    adj = [0] * n
    for v in range(n):
        row = A[v]
        m = 0
        for u in range(n):
            if row[u]:
                m |= 1 << u
        adj[v] = m
    return adj


def _check_lb(adj, order):
    """Check the (LB) 4-point property using bitmask adjacency.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    if n == 0:
        return True
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


def _local_repair(adj, order, affected):
    """Try to repair the ordering by reinserting affected vertices.

    Each affected vertex is removed from the base ordering and then
    reinserted at the earliest position that keeps the (LB) property.
    Returns a new ordering if valid, else None.
    """
    if not affected:
        return order

    aff_set = set(affected)
    base = [v for v in order if v not in aff_set]
    aff = sorted(aff_set)

    new_order = list(base)
    for v in aff:
        placed = False
        for pos in range(len(new_order) + 1):
            trial = new_order[:pos] + [v] + new_order[pos:]
            if _check_lb(adj, trial):
                new_order = trial
                placed = True
                break
        if not placed:
            return None
    if _check_lb(adj, new_order):
        return new_order
    return None


def init(graph):
    A = [list(row) for row in graph]
    adj = _build_adj(A)
    order = _lexbfs_full(A)
    return {'ordering': order, 'A': A, 'adj': adj}


def insert_edge(graph, edge, state):
    A = [list(row) for row in graph]
    u, v = edge

    adj = state['adj']
    # Flip the two bits for the inserted edge.
    adj[u] |= 1 << v
    adj[v] |= 1 << u

    order = state['ordering']
    # The old ordering may still be valid after an insertion.
    if _check_lb(adj, order):
        return {'ordering': order, 'A': A, 'adj': adj}

    # Affected vertices: endpoints plus their common neighbours.
    affected = {u, v}
    common = adj[u] & adj[v]
    x = 0
    while common:
        if common & 1:
            affected.add(x)
        common >>= 1
        x += 1

    new_order = _local_repair(adj, order, affected)
    if new_order is None:
        new_order = _lexbfs_full(A)
    return {'ordering': new_order, 'A': A, 'adj': adj}


def delete_edge(graph, edge, state):
    A = [list(row) for row in graph]
    u, v = edge

    adj = state['adj']
    # Flip the two bits for the deleted edge.
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)

    order = state['ordering']
    # The old ordering may still be valid after a deletion.
    if _check_lb(adj, order):
        return {'ordering': order, 'A': A, 'adj': adj}

    # Affected vertices: endpoints plus their common neighbours.
    affected = {u, v}
    common = adj[u] & adj[v]
    x = 0
    while common:
        if common & 1:
            affected.add(x)
        common >>= 1
        x += 1

    new_order = _local_repair(adj, order, affected)
    if new_order is None:
        new_order = _lexbfs_full(A)
    return {'ordering': new_order, 'A': A, 'adj': adj}
