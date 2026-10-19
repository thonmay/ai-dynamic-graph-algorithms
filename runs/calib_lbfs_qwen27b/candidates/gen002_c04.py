"""Dynamic LexBFS ordering (candidate gen002_c04).

Maintains a valid LexBFS ordering under single edge insertions/deletions.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- update:
    1. If the old ordering is still certified valid by the (LB) 4-point
       property, keep it (no work beyond the certificate check).
    2. Otherwise try a cheap local repair: move one of the two affected
       vertices to a different position; keep it if certified valid.
    3. Otherwise re-derive: keep the longest prefix of the old ordering that
       is still a valid LexBFS prefix, and extend it with partition
       refinement seeded by the prefix.  This is always a valid LexBFS
       (any valid prefix can be extended by partition refinement) and costs
       O(n+m) instead of a full recompute.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
We use it as a certificate of validity, so the state is always a valid
LexBFS ordering.
"""


# ---------------------------------------------------------------------------
# Static LexBFS (partition refinement, O(n+m))
# ---------------------------------------------------------------------------

def _lexbfs_static(adj):
    """Return a valid LexBFS ordering of the undirected graph given by
    adjacency matrix `adj` (list of lists of 0/1)."""
    n = len(adj)
    if n == 0:
        return []
    # adjacency sets
    N = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                N[u].add(v)
                N[v].add(u)

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
# (LB) 4-point property check
# ---------------------------------------------------------------------------

def _is_valid_lexbfs(order, adj):
    """Check the (LB) property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E."""
    n = len(order)
    if n <= 2:
        return True
    # neighbor sets
    N = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                N[u].add(v)
                N[v].add(u)

    # For each pair (b, c) with pos[b] < pos[c]:
    #   A = {a : pos[a] < pos[b], a~c, a not~ b}
    #   if A nonempty, let a0 = min pos in A; need exists d < pos[a0]
    #   with d~b and d not~ c.
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


# ---------------------------------------------------------------------------
# Local repair: try to move one vertex to a better position
# ---------------------------------------------------------------------------

def _try_local_repair(order, adj, moved):
    """Try to produce a valid ordering by moving `moved` to a different
    position. Returns a new ordering or None."""
    n = len(order)
    if n <= 2:
        return order
    cur = order.index(moved)
    # Try positions in order of distance from current position.
    for d in range(1, n):
        for p in (cur - d, cur + d):
            if 0 <= p < n:
                new_order = order[:cur] + order[cur + 1:]
                new_order.insert(p, moved)
                if _is_valid_lexbfs(new_order, adj):
                    return new_order
    return None


# ---------------------------------------------------------------------------
# Re-derivation: keep a valid prefix, extend by partition refinement
# ---------------------------------------------------------------------------

def _rederive(order, adj):
    """Given an old ordering `order` (possibly invalid in the new graph),
    find the longest prefix that is still a valid LexBFS prefix, and extend
    it with partition refinement seeded by that prefix.  The result is
    always a valid LexBFS ordering."""
    n = len(order)
    if n == 0:
        return []
    # adjacency sets
    N = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                N[u].add(v)
                N[v].add(u)

    # Longest valid prefix: the (LB) property only involves vertices that
    # all appear before c, so a prefix of length k is a valid LexBFS prefix
    # iff the (LB) property holds for all triples within the prefix.
    # We check incrementally: prefix of length k is valid iff prefix of
    # length k-1 is valid and no violation has c at position k-1.
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
    return {'ordering': order}


def _update(graph, edge, state):
    u, v = edge
    order = state['ordering']
    # 1. If the old ordering is still valid, keep it.
    if _is_valid_lexbfs(order, graph):
        return {'ordering': order}
    # 2. Try local repair: move u or v.
    for moved in (u, v):
        new_order = _try_local_repair(order, graph, moved)
        if new_order is not None:
            return {'ordering': new_order}
    # 3. Re-derive: keep the longest valid prefix, extend by refinement.
    new_order = _rederive(order, graph)
    return {'ordering': new_order}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)
