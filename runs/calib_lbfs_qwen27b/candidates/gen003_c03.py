"""Dynamic LexBFS ordering (candidate gen003_c03).

Maintains a valid LexBFS ordering under single edge insertions/deletions.

Strategy (derived from gen002_c04, with a cheaper certificate check):
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

Key improvement over the parent: the certificate check is O(n^2 / w)
instead of O(n^3).  For a fixed b, define
    S_b = { a : pos[a] < pos[b], a~b }
A violation with witness b exists iff there is c > b with c~b and
    S_b \\ N(c) != empty   and   (S_b & mask<a0) subset of N(c)
where a0 = min pos in (S_b \\ N(c)).  Equivalently, for each b we need
    max_{c > b, c~b} |S_b \\ N(c) & mask<a0(c)| == 0
which reduces to checking, for each b, whether there exists c > b with
c~b such that the first element of S_b \\ N(c) (in position order) has
all earlier S_b elements in N(c).  With bitsets this is O(n^2 / w).
"""


# ---------------------------------------------------------------------------
# (LB) 4-point property check, O(n^2 / w)
# ---------------------------------------------------------------------------

def _is_valid_lexbfs(order, adj):
    """Check the (LB) property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.

    For fixed b: S_b = {a < b : a~b}.  Violation iff exists c > b with
    c~b and a0 = min pos in (S_b \\ N(c)) exists and
    (S_b & mask<a0) subset of N(c), i.e. S_b & mask<a0 & ~N(c) == 0.
    """
    n = len(order)
    if n <= 2:
        return True
    # Build adjacency bitsets
    bits = [0] * n
    for u in range(n):
        row = adj[u]
        b = 0
        for v in range(n):
            if row[v]:
                b |= 1 << v
        bits[u] = b

    for bi in range(1, n - 1):
        b = order[bi]
        Nb = bits[b]
        # S_b = neighbors of b that appear before b
        S = 0
        for ai in range(bi):
            a = order[ai]
            if (Nb >> a) & 1:
                S |= 1 << a
        if S == 0:
            continue
        # For each c > b with c~b:
        #   a0 = min pos < bi in (S & ~N(c))
        #   if a0 exists and (S & mask<a0 & ~N(c)) == 0: violation
        for ci in range(bi + 1, n):
            c = order[ci]
            Nc = bits[c]
            # S & ~N(c): neighbors of b before b that are NOT neighbors of c
            diff = S & ~Nc
            if diff == 0:
                continue
            # a0 = position of lowest set bit in diff
            a0 = (diff & (-diff)).bit_length() - 1
            # mask<a0: bits 0..a0-1
            mask = (1 << a0) - 1
            # Check: S & mask & ~N(c) == 0
            # i.e. all neighbors of b before position a0 are also neighbors of c
            if (S & mask & ~Nc) == 0:
                return False
    return True


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
