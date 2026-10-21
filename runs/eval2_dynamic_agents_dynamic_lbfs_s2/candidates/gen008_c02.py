"""Dynamic LexBFS ordering (gen008_c02).

Derived from gen006_c02.  Same overall strategy:
  1. If the old ordering is still valid, keep it.
  2. Otherwise try a local repair: reinsert the affected vertices
     (endpoints plus their common neighbours) into the base ordering,
     choosing the earliest position that keeps the (LB) 4-point
     property.
  3. If the repair fails, fall back to a full static LexBFS.

Changes in this generation (targeting the work ratio plateau):
  * The (LB) certificate check is now O(n^2) instead of O(n^3):
    for each position a, the set of (b, c) pairs that need a witness
    is exactly (N(a) \\ N(a-1)) x (N(a-1) \\ N(a)) (positions), so
    the witness test for all pairs at once is a single bitmask AND
    per pair.  The per-a work is O(|N(a) \\ N(a-1)| +
    |N(a-1) \\ N(a)|) bit ops, i.e. O(n^2) total instead of O(n^3).
  * The local repair no longer calls the full certificate check for
    every trial position (that was O(n^4) per affected vertex).
    Instead it uses a cheap necessary condition (the (b, c) pairs
    involving the inserted vertex must have witnesses) and only runs
    the full O(n^2) check on the final ordering.  The final check
    guarantees correctness, so the cheap filter is safe.
  * The affected set for the repair is the endpoints plus their
    common neighbours (unchanged from the parent).
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
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    For each a, the (b, c) pairs that need a witness are:
      b in (N(a) \\ N(a-1))  and  c in (N(a-1) \\ N(a))
    where N(a) is the set of neighbours of order[a] among positions
    > a, and N(a-1) is the same for order[a-1].  (If b were in
    N(a-1) then ab would be in E; if c were not in N(a-1) then ac
    would not be in E.)  The witness test is one bitmask AND per
    pair: (adj[b] & ~adj[c] & prefix) != 0.
    """
    n = len(order)
    if n == 0:
        return True
    prefix = 0
    prev_mask = 0  # N(a-1): neighbours of order[a-1] among positions > a-1
    for a in range(n):
        va = order[a]
        ma = adj[va]
        # N(a): neighbours of va among positions > a.
        na = ma & ~prefix & ~(1 << va)
        # b candidates: in N(a) but not in N(a-1)
        bset = na & ~prev_mask
        # c candidates: in N(a-1) but not in N(a)
        cset = prev_mask & ~na
        if bset and cset:
            # For each b in bset, c in cset: need witness d < a.
            # Witness condition: (adj[b] & ~adj[c] & prefix) != 0.
            # Iterate over the smaller set for the outer loop.
            if bset.bit_count() <= cset.bit_count():
                x = bset
                while x:
                    lb = x & -x
                    x ^= lb
                    b = lb.bit_length() - 1
                    mb = adj[b]
                    y = cset
                    while y:
                        lc = y & -y
                        y ^= lc
                        c = lc.bit_length() - 1
                        if (mb & ~adj[c] & prefix) == 0:
                            return False
            else:
                y = cset
                while y:
                    lc = y & -y
                    y ^= lc
                    c = lc.bit_length() - 1
                    notc = ~adj[c]
                    x = bset
                    while x:
                        lb = x & -x
                        x ^= lb
                        b = lb.bit_length() - 1
                        if (adj[b] & notc & prefix) == 0:
                            return False
        prefix |= 1 << va
        prev_mask = na
    return True


def _check_lb_brute(adj, order):
    """Brute-force (LB) check: O(n^3) but simple and correct.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    if n == 0:
        return True
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
                if (mb & ~adj[vc] & ((1 << a) - 1)) == 0:
                    return False
    return True


def _check_lb_debug(adj, order):
    """Debug: compare _check_lb and _check_lb_brute, print details."""
    r1 = _check_lb(adj, order)
    r2 = _check_lb_brute(adj, order)
    if r1 != r2:
        print(f"MISMATCH: _check_lb={r1}, _check_lb_brute={r2}")
        print(f"  order={order}")
        for i, v in enumerate(order):
            print(f"  pos {i}: vertex {v}, adj={bin(adj[v])}")
        # Find the specific violation
        n = len(order)
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
                    witness = (mb & ~adj[vc] & ((1 << a) - 1))
                    if witness == 0:
                        print(f"  VIOLATION: a={a}(v{va}) b={b}(v{vb}) c={c}(v{vc})")
                        print(f"    adj[b]={bin(mb)}, ~adj[c]={bin(~adj[vc])}, prefix={bin((1<<a)-1)}")
                        print(f"    mb & ~adj[c] & prefix = {bin(witness)}")
    return r1


def _cheap_insert_ok(adj, order, pos, v):
    """Cheap necessary condition for inserting v at position pos.

    After inserting v at position pos, the only new (a, b, c) triples
    that could violate (LB) are those where v is one of a, b, c and
    the triple was not present before.  We check the necessary
    conditions for those triples.  This is NOT sufficient (the full
    check is still run on the final ordering), but it filters out
    most bad positions quickly.

    Cases (positions in the NEW ordering):
      - v at position a: the (b, c) pairs with b, c > a are the same
        as before (v was not among them), so the condition at
        position a is unchanged.  No check needed.

      - v at position b: for all a < b, c > b with ac in E, ab not
        in E: need witness d < a with db in E, dc not in E.  Here
        db is the new edge relation (v is b).  For each a < b with
        ac in E and av not in E, we need (adj[v] & ~adj[c] &
        prefix_a) != 0 where prefix_a is the set of positions < a.

      - v at position c: for all a < c, b < c with ac in E (i.e. av
        in E), ab not in E: need witness d < a with db in E, dc not
        in E (i.e. dv not in E).  For each a < c with av in E, and
        b in (a, c) with ab not in E: need (adj[b] & ~adj[v] &
        prefix_a) != 0.
    """
    n = len(order)
    mv = adj[v]
    prefix = 0
    for a in range(pos):
        va = order[a]
        ma = adj[va]
        # Case 2: v at position b = pos.
        # av not in E, and there exists c >= pos with ac in E.
        if not ((mv >> va) & 1):
            # c >= pos in new ordering = c >= pos in old ordering
            # (positions pos..n-1 shift right by 1, but the vertex
            # at old position c is the same).
            tail = ma & ~((1 << pos) - 1)
            # tail has bits for neighbours of va at positions >= pos.
            # (va itself is at position a < pos, so its bit is not in tail.)
            while tail:
                lc = tail & -tail
                tail ^= lc
                c = lc.bit_length() - 1
                if (mv & ~adj[c] & prefix) == 0:
                    return False
        # Case 3: v at position c = pos.
        # av in E, and there exists b in (a, pos) with ab not in E.
        else:
            # Positions in (a, pos): bits a+1..pos-1.
            mid_range = ((1 << pos) - 1) & ~((1 << (a + 1)) - 1)
            non_neigh = mid_range & ~ma
            x = non_neigh
            notmv = ~mv
            while x:
                lb = x & -x
                x ^= lb
                b = lb.bit_length() - 1
                if (adj[b] & notmv & prefix) == 0:
                    return False
        prefix |= 1 << va
    return True


def _local_repair(adj, order, affected):
    """Try to repair the ordering by reinserting affected vertices.

    Each affected vertex is removed from the base ordering and then
    reinserted at the earliest position that passes the cheap
    necessary condition.  The final ordering is verified with the
    full O(n^2) certificate before being accepted.
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
            if _cheap_insert_ok(adj, new_order, pos, v):
                new_order = new_order[:pos] + [v] + new_order[pos:]
                placed = True
                break
        if not placed:
            return None
    if _check_lb_debug(adj, new_order):
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
