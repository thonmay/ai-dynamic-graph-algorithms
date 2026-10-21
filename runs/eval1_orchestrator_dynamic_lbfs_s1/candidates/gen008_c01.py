"""Dynamic LexBFS ordering (open problem; correctness-first candidate).

Strategy: maintain a valid LexBFS ordering.  After each update, try to
repair the existing ordering with local fixes (transpositions and small
moves); if no local fix restores validity, fall back to a full
O(n^2) partition-refinement recomputation.

Validity is certified by the (LB) 4-point property of Corneil and
Krueger: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.

The validity check is O(n^3) using integer bitsets: for each b, the
set of positions d < a with db in E and dc not in E is
  (N(b) & ~N(c)) & ((1 << a) - 1)
which is non-empty exactly when the property holds.
"""


def _check_lexbfs(graph, order):
    """Return True iff `order` is a valid LexBFS ordering of `graph`.

    Uses the (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.
    O(n^3) with integer bitsets.
    """
    n = len(order)
    if n == 0:
        return True
    # N[v] = bitset of positions of neighbors of order[v]
    N = [0] * n
    for v in range(n):
        ov = order[v]
        bits = 0
        row = graph[ov]
        for w in range(n):
            if row[order[w]]:
                bits |= 1 << w
        N[v] = bits
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue  # ab in E: condition vacuous
            # ab not in E; for every c > b with ac in E, need
            # (N[b] & ~N[c]) & ((1 << a) - 1) != 0
            mask = (1 << a) - 1
            nb = N[b]
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue
                if (nb & ~N[c] & mask) == 0:
                    return False
    return True





def _lexbfs_full(graph):
    """Full O(n^2) LexBFS via partition refinement with buckets.

    Returns a valid LexBFS ordering (deterministic tie-break by vertex id).
    """
    n = len(graph)
    if n == 0:
        return []
    # buckets: list of lists of vertices, in order.
    # Initially one bucket containing all vertices (all labels empty).
    buckets = [list(range(n))]

    ordered = []
    while buckets:
        # take first vertex of first bucket
        b = buckets[0]
        v = b[0]
        b.remove(v)
        if not b:
            buckets.pop(0)
        ordered.append(v)
        # refine all buckets by adjacency to v
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            adj_part = [x for x in bucket if graph[v][x]]
            non_part = [x for x in bucket if not graph[v][x]]
            # adjacent part first (they get the 1 bit for v)
            if adj_part:
                new_buckets.append(adj_part)
            if non_part:
                new_buckets.append(non_part)
        buckets = new_buckets
    return ordered


def _try_transpose(order, u, v):
    """Return a new order with u and v swapped, or None if not adjacent
    in the order."""
    pos = {x: i for i, x in enumerate(order)}
    i, j = pos[u], pos[v]
    if abs(i - j) != 1:
        return None
    new = list(order)
    new[i], new[j] = new[j], new[i]
    return new


def _try_move(order, x, i):
    """Return a new order with vertex x moved to position i (x currently
    at some other position)."""
    pos = {v: k for k, v in enumerate(order)}
    j = pos[x]
    if j == i:
        return None
    new = list(order)
    new.pop(j)
    new.insert(i, x)
    return new


def _repair(graph, order, edge):
    """Try to repair `order` after flipping `edge`.  Return a valid
    ordering or None."""
    u, v = edge
    if _check_lexbfs(graph, order):
        return order
    # try transposition of u and v if adjacent in order
    cand = _try_transpose(order, u, v)
    if cand is not None and _check_lexbfs(graph, cand):
        return cand
    # try moving the later of u,v just before the earlier one
    pos = {x: i for i, x in enumerate(order)}
    i, j = pos[u], pos[v]
    if i > j:
        i, j = j, i  # i is earlier position, j later
    # move vertex at position j to position i
    new = list(order)
    x = new.pop(j)
    new.insert(i, x)
    if _check_lexbfs(graph, new):
        return new
    # try moving the earlier of u,v just after the later one
    new = list(order)
    x = new.pop(i)
    new.insert(j + 1, x)
    if _check_lexbfs(graph, new):
        return new
    # try moving u to each of a few nearby positions
    for target in (i - 1, i + 1, j, j + 1):
        if 0 <= target < len(order):
            cand = _try_move(order, u, target)
            if cand is not None and _check_lexbfs(graph, cand):
                return cand
    # try moving v to each of a few nearby positions
    for target in (j - 1, j + 1, i, i + 1):
        if 0 <= target < len(order):
            cand = _try_move(order, v, target)
            if cand is not None and _check_lexbfs(graph, cand):
                return cand
    # try all adjacent transpositions (cheap, O(n) checks)
    for k in range(len(order) - 1):
        new = list(order)
        new[k], new[k + 1] = new[k + 1], new[k]
        if _check_lexbfs(graph, new):
            return new
    # try moving u to every position
    for target in range(len(order)):
        cand = _try_move(order, u, target)
        if cand is not None and _check_lexbfs(graph, cand):
            return cand
    # try moving v to every position
    for target in range(len(order)):
        cand = _try_move(order, v, target)
        if cand is not None and _check_lexbfs(graph, cand):
            return cand
    # try moving every vertex to every position (exhaustive single-move
    # search; guarantees a fix whenever one exists)
    for x in order:
        for target in range(len(order)):
            cand = _try_move(order, x, target)
            if cand is not None and _check_lexbfs(graph, cand):
                return cand
    # try all pairs of adjacent transpositions (two adjacent swaps)
    m = len(order)
    for k in range(m - 1):
        for l in range(m - 1):
            new = list(order)
            new[k], new[k + 1] = new[k + 1], new[k]
            new[l], new[l + 1] = new[l + 1], new[l]
            if _check_lexbfs(graph, new):
                return new
    # try all pairs of single moves (move x to i, then y to j)
    for x in order:
        for i in range(m):
            base = _try_move(order, x, i)
            if base is None:
                continue
            for y in order:
                for j in range(m):
                    cand = _try_move(base, y, j)
                    if cand is not None and _check_lexbfs(graph, cand):
                        return cand
    # try all triples of single moves (move x to i, then y to j, then z to k)
    for x in order:
        for i in range(m):
            base1 = _try_move(order, x, i)
            if base1 is None:
                continue
            for y in order:
                for j in range(m):
                    base2 = _try_move(base1, y, j)
                    if base2 is None:
                        continue
                    for z in order:
                        for k in range(m):
                            cand = _try_move(base2, z, k)
                            if cand is not None and _check_lexbfs(graph, cand):
                                return cand
    return None


def init(graph):
    order = _lexbfs_full(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    fixed = _repair(graph, order, edge)
    if fixed is None:
        fixed = _lexbfs_full(graph)
    return {'ordering': fixed}


def delete_edge(graph, edge, state):
    order = state['ordering']
    fixed = _repair(graph, order, edge)
    if fixed is None:
        fixed = _lexbfs_full(graph)
    return {'ordering': fixed}
