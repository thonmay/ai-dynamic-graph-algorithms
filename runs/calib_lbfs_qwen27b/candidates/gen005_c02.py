"""Dynamic LexBFS ordering (candidate gen005_c02).

Maintains a valid LexBFS ordering under single edge insertions/deletions.

Strategy (cheapest first):
  1. If the old ordering is still certified valid by the (LB) 4-point
     property, keep it (no work beyond the certificate check).
  2. Otherwise try a cheap *targeted* local repair: for each violating
     (a,b,c) triple, the only single-vertex moves that can fix it are
     "move b before a" or "move c after b".  We try exactly those O(n)
     candidate positions (each verified by a fast O(n^2) certificate
     check) and keep the first valid one.
  3. Otherwise re-derive: keep the longest prefix of the old ordering that
     is still a valid LexBFS prefix (found incrementally in O(n^2)), and
     extend it with partition refinement seeded by the prefix.  This is
     always a valid LexBFS (any valid prefix can be extended by partition
     refinement) and costs O(n+m) instead of a full recompute.
  4. Safety net: if the re-derivation ever fails its own certificate
     check, fall back to a full static recompute.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
We use it as a certificate of validity, so the state is always a valid
LexBFS ordering.

State: {'ordering': list, 'N': list of neighbor sets (cached, updated
incrementally per edge flip)}.
"""


# ---------------------------------------------------------------------------
# Static LexBFS (partition refinement, O(n+m))
# ---------------------------------------------------------------------------

def _adjacency_sets(adj):
    """Build neighbor sets from a 0/1 adjacency matrix."""
    n = len(adj)
    N = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                N[u].add(v)
                N[v].add(u)
    return N


def _lexbfs_static(adj):
    """Return a valid LexBFS ordering of the undirected graph given by
    adjacency matrix `adj` (list of lists of 0/1)."""
    n = len(adj)
    if n == 0:
        return []
    N = _adjacency_sets(adj)

    # buckets: list of sets, each bucket is a set of vertices
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # pick first non-empty bucket
        i = 0
        while i < len(buckets) and not buckets[i]:
            i += 1
        if i == len(buckets):
            break
        B = buckets[i]
        # choose smallest vertex in B
        v = min(B)
        B.remove(v)
        order.append(v)
        # refine each bucket by adjacency to v
        new_buckets = []
        for C in buckets:
            if not C:
                continue
            Cn = set()
            Cnot = set()
            for x in C:
                if x in N[v]:
                    Cn.add(x)
                else:
                    Cnot.add(x)
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets
    return order


# ---------------------------------------------------------------------------
# (LB) 4-point property check (certificate)
# ---------------------------------------------------------------------------

def _is_valid_lexbfs(order, N):
    """Check the (LB) property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.

    N: list of neighbor sets (cached).  O(n^2) set lookups.
    """
    n = len(order)
    if n <= 2:
        return True
    for ci in range(n):
        c = order[ci]
        Nc = N[c]
        for bi in range(ci):
            b = order[bi]
            Nb = N[b]
            # find a: pos < bi, a in Nc, a not in Nb
            a0 = None
            for ai in range(bi):
                a = order[ai]
                if a in Nc and a not in Nb:
                    a0 = ai
                    break
            if a0 is None:
                continue
            # need d < a0 with d in Nb and d not in Nc
            ok = False
            for di in range(a0):
                d = order[di]
                if d in Nb and d not in Nc:
                    ok = True
                    break
            if not ok:
                return False
    return True


def _violations(order, N):
    """Return the list of violating (a, b, c) position triples:
    a < b < c, ac in E, ab not in E, and no d < a with db in E and
    dc not in E.  O(n^2)."""
    n = len(order)
    out = []
    for ci in range(n):
        c = order[ci]
        Nc = N[c]
        for bi in range(ci):
            b = order[bi]
            Nb = N[b]
            a0 = None
            for ai in range(bi):
                a = order[ai]
                if a in Nc and a not in Nb:
                    a0 = ai
                    break
            if a0 is None:
                continue
            ok = False
            for di in range(a0):
                d = order[di]
                if d in Nb and d not in Nc:
                    ok = True
                    break
            if not ok:
                out.append((a0, bi, ci))
    return out


# ---------------------------------------------------------------------------
# Targeted local repair
# ---------------------------------------------------------------------------

def _try_local_repair(order, N):
    """Try to produce a valid ordering by moving a single vertex to a
    position that can fix at least one violating triple.

    For a violation (a, b, c) the only single-vertex moves that can fix
    it are: move b to a position < a, or move c to a position > b.
    We collect all such candidate (vertex, target) pairs and try them in
    order of distance from the vertex's current position, verifying each
    with the O(n^2) certificate.  Returns a new ordering or None.
    """
    n = len(order)
    if n <= 2:
        return order
    viols = _violations(order, N)
    if not viols:
        return order

    pos = {v: i for i, v in enumerate(order)}
    cands = set()
    for (a, b, c) in viols:
        vb = order[b]
        vc = order[c]
        # move b before a: target positions 0..a-1
        for p in range(a):
            cands.add((vb, p))
        # move c after b: target positions b+1..n-1
        for p in range(b + 1, n):
            cands.add((vc, p))

    # order candidates by distance from current position
    cands = sorted(cands, key=lambda t: abs(pos[t[0]] - t[1]))

    for (v, p) in cands:
        cur = pos[v]
        if p == cur:
            continue
        new_order = order[:cur] + order[cur + 1:]
        new_order.insert(p, v)
        if _is_valid_lexbfs(new_order, N):
            return new_order
    return None


# ---------------------------------------------------------------------------
# Re-derivation: keep a valid prefix, extend by partition refinement
# ---------------------------------------------------------------------------

def _rederive(order, N):
    """Given an old ordering `order` (possibly invalid in the new graph),
    find the longest prefix that is still a valid LexBFS prefix, and extend
    it with partition refinement seeded by that prefix.  The result is
    always a valid LexBFS ordering.

    The prefix search is incremental: a prefix of length k is valid iff
    the prefix of length k-1 is valid and no violation has c at position
    k-1.  Total O(n^2).
    """
    n = len(order)
    if n == 0:
        return []

    # Longest valid prefix, checked incrementally.
    k = 0
    for k in range(1, n + 1):
        # check violations with c = order[k-1]
        c = order[k - 1]
        Nc = N[c]
        bad = False
        for bi in range(k - 1):
            b = order[bi]
            Nb = N[b]
            a0 = None
            for ai in range(bi):
                a = order[ai]
                if a in Nc and a not in Nb:
                    a0 = ai
                    break
            if a0 is None:
                continue
            ok = False
            for di in range(a0):
                d = order[di]
                if d in Nb and d not in Nc:
                    ok = True
                    break
            if not ok:
                bad = True
                break
        if bad:
            k -= 1
            break
    # k is the length of the longest valid prefix
    prefix = order[:k]
    remaining = [v for v in order[k:]]
    if not remaining:
        return order

    # Seed buckets: refine the remaining set by adjacency to each prefix
    # vertex, in prefix order.  This is exactly the state the partition
    # refinement would have reached after processing the prefix.
    buckets = [set(remaining)]
    for p in prefix:
        Np = N[p]
        new_buckets = []
        for C in buckets:
            if not C:
                continue
            Cn = set()
            Cnot = set()
            for x in C:
                if x in Np:
                    Cn.add(x)
                else:
                    Cnot.add(x)
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets

    # Continue partition refinement on the remaining vertices.
    for _ in range(len(remaining)):
        i = 0
        while i < len(buckets) and not buckets[i]:
            i += 1
        if i == len(buckets):
            break
        B = buckets[i]
        v = min(B)
        B.remove(v)
        prefix.append(v)
        new_buckets = []
        for C in buckets:
            if not C:
                continue
            Cn = set()
            Cnot = set()
            for x in C:
                if x in N[v]:
                    Cn.add(x)
                else:
                    Cnot.add(x)
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets
    return prefix


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def init(graph):
    order = _lexbfs_static(graph)
    return {'ordering': order, 'N': _adjacency_sets(graph)}


def _update(graph, edge, state):
    u, v = edge
    N = state['N']
    # Update the cached neighbor sets for the flipped edge.
    if graph[u][v]:
        N[u].add(v)
        N[v].add(u)
    else:
        N[u].discard(v)
        N[v].discard(u)

    order = state['ordering']
    # 1. If the old ordering is still valid, keep it.
    if _is_valid_lexbfs(order, N):
        return {'ordering': order, 'N': N}
    # 2. Try targeted local repair.
    new_order = _try_local_repair(order, N)
    if new_order is not None:
        return {'ordering': new_order, 'N': N}
    # 3. Re-derive: keep the longest valid prefix, extend by refinement.
    new_order = _rederive(order, N)
    # 4. Safety net: the re-derivation must be valid; if the certificate
    #    disagrees (should not happen), fall back to a full static
    #    recompute.
    if not _is_valid_lexbfs(new_order, N):
        new_order = _lexbfs_static(graph)
    return {'ordering': new_order, 'N': N}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)
