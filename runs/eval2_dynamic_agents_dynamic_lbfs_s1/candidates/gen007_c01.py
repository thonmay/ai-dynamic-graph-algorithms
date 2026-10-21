"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static LexBFS via partition refinement (O(n^2) bitset version).
- insert_edge(u, v) / delete_edge(u, v): a single edge flip only affects
  (LB) 4-point triples that involve the flipped edge, so we run a
  *targeted* validity check (O(n^2) worst case, early-exit) instead of the
  parent's O(n^3) full check.  If the ordering is still valid we keep it;
  otherwise we recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

Targeted check after flipping edge (u, v):
  Let p = pos[u], q = pos[v], assume p < q.
  - Necessary condition: the (p, q) pair itself must be (LB)-satisfied
    (this is the only pair whose own status can change).
  - For every c > q: the witness set for pair (u, c) gains/loses v, and
    the violation set for pair (v, c) gains/loses u.  Both are checked
    in O(n) each.
  - For every b < p: the violation set for pair (b, u) gains/loses v,
    and for pair (b, v) gains/loses u.  Checked in O(n) each.
  - All other pairs are unaffected by the flip.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list.

    O(n^2) using bitsets: each bucket is a Python int bitmask of its
    members; refinement of a bucket by vertex v is a single AND.
    """
    n = len(graph)
    if n == 0:
        return []

    # Bitset of neighbors of each vertex.
    nbr = [0] * n
    for i in range(n):
        row = graph[i]
        m = 0
        for j in range(n):
            if row[j]:
                m |= 1 << j
        nbr[i] = m

    buckets = [(1 << n) - 1]
    ordering = []

    for _ in range(n):
        # Find the first non-empty bucket.
        bi = 0
        while bi < len(buckets) and buckets[bi] == 0:
            bi += 1
        if bi >= len(buckets):
            break

        # Take the lowest-numbered vertex of this bucket (deterministic
        # tie-break; any tie-break is valid).
        b = buckets[bi]
        v = (b & -b).bit_length() - 1
        buckets[bi] = b ^ (1 << v)
        ordering.append(v)

        # Refine every remaining bucket by adjacency to v.
        nb = nbr[v]
        new_buckets = []
        for x in buckets:
            if x == 0:
                continue
            a = x & nb
            c = x & ~nb
            if a:
                new_buckets.append(a)
            if c:
                new_buckets.append(c)
        buckets = new_buckets

    return ordering


def _recompute(graph):
    """Recompute the LexBFS ordering from scratch."""
    return {'ordering': _lexbfs(graph)}


def _check_pair(graph, ordering, i, j):
    """Check the (LB) condition for the pair (ordering[i], ordering[j]),
    i < j.  O(j^2) worst case."""
    n = len(ordering)
    b = ordering[i]
    c = ordering[j]
    # Find the minimum position d < i with graph[d][b]=1 and graph[d][c]=0.
    min_d = n
    for d in range(i):
        x = ordering[d]
        if graph[x][b] and not graph[x][c]:
            min_d = d
            break
    # For every a < i with graph[a][c]=1 and graph[a][b]=0 we need a > min_d.
    for a in range(i):
        x = ordering[a]
        if graph[x][c] and not graph[x][b]:
            if a <= min_d:
                return False
    return True


def _still_valid_after_flip(graph, ordering, u, v):
    """Targeted (LB) check after flipping edge (u, v).  O(n^2) worst case."""
    n = len(ordering)
    if n <= 2:
        return True

    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i

    p = pos[u]
    q = pos[v]
    if p > q:
        p, q = q, p

    # 1. Necessary condition: the (p, q) pair itself must be satisfied.
    if not _check_pair(graph, ordering, p, q):
        return False

    # 2. Pairs (u, c) and (v, c) for c > q: their witness sets change.
    for ci in range(q + 1, n):
        c = ordering[ci]
        # Pair (u, c): violation set = {a < p : a~c, a not~ u}.
        # u is in it iff graph[u][c] (and not graph[u][u]).
        # If u is a violator, we need a witness d < p with d~u, d not~ c.
        if graph[u][c]:
            ok = False
            for d in range(p):
                x = ordering[d]
                if graph[x][u] and not graph[x][c]:
                    ok = True
                    break
            if not ok:
                return False
        # Pair (v, c): violation set = {a < q : a~c, a not~ v}.
        # v is in it iff graph[v][c].
        if graph[v][c]:
            ok = False
            for d in range(q):
                x = ordering[d]
                if graph[x][v] and not graph[x][c]:
                    ok = True
                    break
            if not ok:
                return False

    # 3. Pairs (b, u) and (b, v) for b < p: their violation sets change.
    for bi in range(p):
        b = ordering[bi]
        # Pair (b, u): violation set = {a < bi : a~u, a not~ b}.
        # v is in it iff graph[v][u] and not graph[v][b].
        # If v is a violator, need witness d < bi with d~b, d not~ u.
        if graph[v][u] and not graph[v][b]:
            ok = False
            for d in range(bi):
                x = ordering[d]
                if graph[x][b] and not graph[x][u]:
                    ok = True
                    break
            if not ok:
                return False
        # Pair (b, v): violation set = {a < bi : a~v, a not~ b}.
        # u is in it iff graph[u][v] and not graph[u][b].
        if graph[u][v] and not graph[u][b]:
            ok = False
            for d in range(bi):
                x = ordering[d]
                if graph[x][b] and not graph[x][v]:
                    ok = True
                    break
            if not ok:
                return False

    return True


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    return _recompute(graph)


def insert_edge(graph, edge, state):
    """Handle edge insertion. Keep the ordering if still valid."""
    u, v = edge
    if _still_valid_after_flip(graph, state['ordering'], u, v):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    """Handle edge deletion. Keep the ordering if still valid."""
    u, v = edge
    if _still_valid_after_flip(graph, state['ordering'], u, v):
        return state
    return _recompute(graph)
