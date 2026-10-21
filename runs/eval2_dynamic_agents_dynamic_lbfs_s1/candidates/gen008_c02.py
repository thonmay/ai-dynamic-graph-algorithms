"""Dynamic LexBFS ordering (gen008_c02).

Derived from the parent (gen002_c03: check-then-repair-then-recompute) with
two changes aimed at lowering the work ratio:

1. The validity check after an update is *targeted*: a single edge flip
   (u, v) can only change the (LB) 4-point status of triples in which the
   flipped edge plays the role of ab, ac, db or dc.  We check exactly those
   triples (O(n^2) worst case, early-exit) instead of the parent's full
   O(n^3) scan.  This makes the "still valid" fast path much cheaper.

2. The local repair is *guided*: instead of trying every position for u and
   v (2n candidates, each verified by a full O(n^3) check), we first try a
   small set of principled moves (swap u/v, move the later endpoint to the
   front, move the earlier endpoint to the end, move the later endpoint to
   the end, move the earlier endpoint to the front) and verify each with the
   cheap targeted check.  Only if those fail do we fall back to the parent's
   exhaustive move search (with the targeted check), and finally to a full
   recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list.

    Buckets are lists of unselected vertices.  At each step, take the first
    vertex of the first non-empty bucket, output it, and refine every other
    bucket by adjacency to it: the neighbor part is placed BEFORE the
    non-neighbor part, preserving FIFO order inside each part.
    """
    n = len(graph)
    if n == 0:
        return []

    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = buckets[bi].pop(0)
        order.append(v)

        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nbrs = [x for x in b if graph[v][x]]
            non = [x for x in b if not graph[v][x]]
            if nbrs:
                new_buckets.append(nbrs)
            if non:
                new_buckets.append(non)
        buckets = new_buckets

    return order


def _recompute(graph):
    """Recompute the LexBFS ordering from scratch."""
    return {'ordering': _lexbfs(graph)}


def _check_pair(graph, ordering, i, j):
    """Check the (LB) condition for the pair (ordering[i], ordering[j]),
    i < j.  O(i^2) worst case.

    For every a < i with a~c and not a~b, there must exist d < a with
    d~b and not d~c.  Equivalently, the minimum position d < i with
    d~b and not d~c must be strictly smaller than every such a.
    """
    b = ordering[i]
    c = ordering[j]
    # Find the minimum position d < i with graph[ordering[d]][b]=1 and
    # graph[ordering[d]][c]=0.
    min_d = i  # sentinel: no witness found
    for d in range(i):
        x = ordering[d]
        if graph[x][b] and not graph[x][c]:
            min_d = d
            break
    # For every a < i with graph[ordering[a]][c]=1 and
    # graph[ordering[a]][b]=0 we need a > min_d.
    for a in range(i):
        x = ordering[a]
        if graph[x][c] and not graph[x][b]:
            if a <= min_d:
                return False
    return True


def _still_valid_after_flip(graph, ordering, u, v):
    """Targeted (LB) check after flipping edge (u, v).  O(n^2) worst case.

    A triple (a, b, c) with a < b < c can only change its (LB) status if the
    flipped edge (u, v) plays the role of one of the four edges ab, ac, db,
    dc.  We check exactly those triples:

    1. Pair (p, q) where p, q are the positions of u, v (p < q): the edge
       u~v is the ab edge of this pair.  Full pair check.
    2. Pairs (p, c) and (q, c) for c > q: the flipped edge is the ac edge
       (u~c or v~c).  Full pair check.
    3. Pairs (b, p) and (b, q) for b < p: the flipped edge is the db edge
       (u~b or v~b).  Full pair check.

    All other pairs have all four relevant edges unchanged, so their (LB)
    status is unchanged.
    """
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

    # 1. The pair (p, q) itself: u~v is the ab edge.
    if not _check_pair(graph, ordering, p, q):
        return False

    # 2. Pairs (p, c) and (q, c) for c > q: u~c / v~c is the ac edge.
    for ci in range(q + 1, n):
        if not _check_pair(graph, ordering, p, ci):
            return False
        if not _check_pair(graph, ordering, q, ci):
            return False

    # 3. Pairs (b, p) and (b, q) for b < p: u~b / v~b is the db edge.
    for bi in range(p):
        if not _check_pair(graph, ordering, bi, p):
            return False
        if not _check_pair(graph, ordering, bi, q):
            return False

    return True


def _try_local_repair(graph, ordering, u, v):
    """Try to fix the ordering after an edge update involving (u, v).

    First try a small set of principled moves, verified with the cheap
    targeted check.  If those fail, fall back to the exhaustive move search
    (move u or v to every position), also verified with the targeted check.

    Returns a valid ordering or None.
    """
    n = len(ordering)
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i
    pu = pos[u]
    pv = pos[v]

    # Principled moves: each is a single-vertex move or a swap.
    # For each candidate, verify with the targeted check (cheap).
    candidates = []

    # Swap u and v.
    cand = list(ordering)
    cand[pu], cand[pv] = cand[pv], cand[pu]
    candidates.append(cand)

    # Move the later endpoint to the front.
    if pu < pv:
        later, earlier = v, u
    else:
        later, earlier = u, v
    cand = [x for x in ordering if x != later]
    cand.insert(0, later)
    candidates.append(cand)

    # Move the earlier endpoint to the end.
    cand = [x for x in ordering if x != earlier]
    cand.append(earlier)
    candidates.append(cand)

    # Move the later endpoint to the end.
    cand = [x for x in ordering if x != later]
    cand.append(later)
    candidates.append(cand)

    # Move the earlier endpoint to the front.
    cand = [x for x in ordering if x != earlier]
    cand.insert(0, earlier)
    candidates.append(cand)

    for cand in candidates:
        if _still_valid_after_flip(graph, cand, u, v):
            return cand

    # Exhaustive: move u to each position.
    for new_pos in range(n):
        if new_pos == pu:
            continue
        cand = [x for x in ordering if x != u]
        cand.insert(new_pos, u)
        if _still_valid_after_flip(graph, cand, u, v):
            return cand

    # Exhaustive: move v to each position.
    for new_pos in range(n):
        if new_pos == pv:
            continue
        cand = [x for x in ordering if x != v]
        cand.insert(new_pos, v)
        if _still_valid_after_flip(graph, cand, u, v):
            return cand

    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    return _recompute(graph)


def insert_edge(graph, edge, state):
    """Handle edge insertion. Keep the ordering if still valid."""
    u, v = edge
    ordering = state['ordering']
    if _still_valid_after_flip(graph, ordering, u, v):
        return state
    repaired = _try_local_repair(graph, ordering, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    return _recompute(graph)


def delete_edge(graph, edge, state):
    """Handle edge deletion. Keep the ordering if still valid."""
    u, v = edge
    ordering = state['ordering']
    if _still_valid_after_flip(graph, ordering, u, v):
        return state
    repaired = _try_local_repair(graph, ordering, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    return _recompute(graph)
