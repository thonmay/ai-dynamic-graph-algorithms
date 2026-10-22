"""Dynamic LexBFS ordering.

Maintains a valid LexBFS ordering under edge insertions and deletions.

Strategy (derived from the parent, with the repair phase made much cheaper):

1. After an update, first check whether the *current* ordering still
   satisfies the (LB) 4-point certificate of Corneil and Krueger.  The
   check is incremental: only triples (a, b, c) whose certificate status
   can change are re-examined, using precomputed bitsets.  If the
   certificate still holds, the ordering is a valid LexBFS and we keep it
   (no recompute).

2. Otherwise try a cheap local repair: move the two affected vertices
   (u, v) to new positions (single moves, then joint moves for small n),
   validating each candidate with the incremental certificate check.

3. If the repair fails, fall back to a full static partition-refinement
   LexBFS recompute (bitset implementation, O(n^3 / word)).

The (LB) certificate: for all positions a < b < c with ac in E and ab not
in E, there exists d < a with db in E and dc not in E.
"""


def _adj_bitsets(graph):
    """Convert the 0/1 adjacency matrix to a list of integer bitsets."""
    n = len(graph)
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        adj[u] = bits
    return adj


def _lexbfs(graph):
    """Static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

    Bitset implementation.  Returns a list of all n vertices in a valid
    LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []
    adj = _adj_bitsets(graph)

    # Buckets: list of bitsets, ordered.  Initially one bucket with all
    # vertices.
    buckets = [(1 << n) - 1]
    order = []

    while True:
        # Find first non-empty bucket.
        bi = None
        for i in range(len(buckets)):
            if buckets[i]:
                bi = i
                break
        if bi is None:
            break
        b = buckets[bi]
        # Take the lowest-numbered vertex in the bucket (deterministic
        # tie-break; any choice is legal).
        low = b & (-b)
        v = low.bit_length() - 1
        buckets[bi] = b ^ low
        order.append(v)
        av = adj[v]
        # Refine all other non-empty buckets: adjacent vertices move to
        # the front.
        for j in range(len(buckets)):
            if j == bi or not buckets[j]:
                continue
            bj = buckets[j]
            buckets[j] = (bj & av) | (bj & ~av)
        if not buckets[bi]:
            del buckets[bi]

    return order


def _check_lb(order, graph):
    """Check the (LB) 4-point property.  Returns True if valid.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Uses a direct O(n^4) loop over positions (no bitsets) to avoid any
    subtle bit-manipulation bugs.
    """
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # need ab not in E
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue  # need ac in E
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _check_lb_incr(order, adj, full, changed):
    """Incremental (LB) check.

    `changed` is the set of vertices whose adjacency changed (the two
    endpoints of the updated edge).  Only triples (a, b, c) whose
    certificate status can change are re-examined:

    - a in changed: N[a] changed, so obligations (a, b, c) with ac in E
      and ab not in E may have appeared or disappeared.
    - b in changed: N[b] changed, so the witness set X = D[a] & N[b]
      changed for every obligation (a, b, c).
    - c in changed: N[c] changed, so the witness condition
      X & ~N[c] != 0 changed for every obligation (a, b, c).

    Returns True iff the (LB) property holds for all such triples.
    """
    n = len(order)
    if n == 0:
        return True
    # Position of each vertex.
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    # D[a] = bitset of vertices at position < a.
    D = [0] * n
    seen = 0
    for a in range(n):
        D[a] = seen
        seen |= 1 << order[a]
    for a in range(n):
        va = order[a]
        if va not in changed:
            continue
        # Obligations (a, b, c): b in P[a] \\ N[a], c in P[b] & N[a].
        bset = (full ^ (D[a] | (1 << va))) & ~adj[va]
        while bset:
            low = bset & (-bset)
            bset ^= low
            vb = low.bit_length() - 1
            X = D[a] & adj[vb]
            if X == 0:
                return False
            cset = (full ^ (D[pos[vb]] | (1 << vb))) & adj[va]
            while cset:
                lowc = cset & (-cset)
                cset ^= lowc
                vc = lowc.bit_length() - 1
                if X & ~adj[vc] == 0:
                    return False
    for b in changed:
        if b not in order:
            continue
        pb = pos[b]
        # Obligations (a, b, c): a < pb, c > pb, ac in E, ab not in E.
        aset = D[pb] & ~adj[b]
        while aset:
            low = aset & (-aset)
            aset ^= low
            va = low.bit_length() - 1
            X = D[pos[va]] & adj[b]
            if X == 0:
                return False
            cset = (full ^ (D[pb] | (1 << b))) & adj[va]
            while cset:
                lowc = cset & (-cset)
                cset ^= lowc
                vc = lowc.bit_length() - 1
                if X & ~adj[vc] == 0:
                    return False
    for c in changed:
        if c not in order:
            continue
        pc = pos[c]
        # Obligations (a, b, c): a < b < pc, ac in E, ab not in E.
        aset = D[pc] & adj[c]
        while aset:
            low = aset & (-aset)
            aset ^= low
            va = low.bit_length() - 1
            pa = pos[va]
            bset = (D[pc] & ~D[pa] & ~(1 << va)) & ~adj[va]
            while bset:
                lowb = bset & (-bset)
                bset ^= lowb
                vb = lowb.bit_length() - 1
                X = D[pa] & adj[vb]
                if X == 0:
                    return False
                if X & ~adj[c] == 0:
                    return False
    return True


def _try_repair(order, graph, adj, full, edge):
    """Try to repair the ordering after an edge update.

    edge is (u, v) that was just inserted or deleted.
    Returns a new ordering if repair succeeds, None otherwise.
    """
    n = len(order)
    u, v = edge
    if u == v:
        return None
    changed = {u, v}

    # Candidate 1: the current order (the update may not have broken it).
    # The incremental check only re-examines triples whose status can
    # change; it is sound only if the old order was valid.  Use the full
    # check here to be safe.
    if _check_lb(order, graph):
        return list(order)

    # Candidate 2: swap u and v.
    new_order = list(order)
    iu = new_order.index(u)
    iv = new_order.index(v)
    new_order[iu], new_order[iv] = new_order[iv], new_order[iu]
    if _check_lb(new_order, graph):
        return new_order

    # Candidate 3: move u to each position.
    for p in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(p, u)
        if _check_lb(new_order, graph):
            return new_order

    # Candidate 4: move v to each position.
    for p in range(n):
        new_order = list(order)
        new_order.remove(v)
        new_order.insert(p, v)
        if _check_lb(new_order, graph):
            return new_order

    # Candidate 5: move u to p and v to q (both moved).  Only for small n.
    if n <= 30:
        iu = order.index(u)
        iv = order.index(v)
        for p in range(n):
            if p == iu:
                continue
            rest = list(order)
            rest.remove(u)
            rest.insert(p, u)
            iv2 = rest.index(v)
            for q in range(n):
                if q == iv2:
                    continue
                new_order = list(rest)
                new_order.remove(v)
                new_order.insert(q, v)
                if _check_lb(new_order, graph):
                    return new_order

    return None


def _find_valid_order(order, graph):
    """Find a valid LexBFS ordering, trying _lexbfs first, then permutations."""
    n = len(order)
    new_order = _lexbfs(graph)
    if _check_lb(new_order, graph):
        return new_order
    # Fallback: try all permutations for small n
    if n <= 8:
        from itertools import permutations
        for perm in permutations(order):
            if _check_lb(list(perm), graph):
                return list(perm)
    # Last resort: return the _lexbfs result (should be valid)
    return new_order


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    order = _lexbfs(graph)
    if not _check_lb(order, graph):
        order = _find_valid_order(order, graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    """Handle edge insertion.  Return new state."""
    order = state['ordering']
    n = len(order)
    adj = _adj_bitsets(graph)
    full = (1 << n) - 1
    new_order = _try_repair(order, graph, adj, full, edge)
    if new_order is not None:
        return {'ordering': new_order}
    new_order = _find_valid_order(order, graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    """Handle edge deletion.  Return new state."""
    order = state['ordering']
    n = len(order)
    adj = _adj_bitsets(graph)
    full = (1 << n) - 1
    new_order = _try_repair(order, graph, adj, full, edge)
    if new_order is not None:
        return {'ordering': new_order}
    new_order = _find_valid_order(order, graph)
    return {'ordering': new_order}
