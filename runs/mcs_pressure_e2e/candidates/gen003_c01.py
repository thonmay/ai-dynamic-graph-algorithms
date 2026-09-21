"""Dynamic Maximum Cardinality Search (MCS) ordering, undirected graphs.

Maintains a vertex ordering that is a valid MCS ordering of the current
graph: each vertex is chosen when its cardinality (number of already-chosen
neighbors) is maximal among the unchosen vertices (ties broken by smallest id).

Approach (fully dynamic, tight affected window, bitset buckets): adjacency is
one bitmask per vertex, so flipping edge (u, v) is two int ops. Let pos[u] <
pos[v]. The flip changes the selection-time cardinality of exactly one vertex,
v, and only for prefixes that contain u, i.e. from step pos[u] + 1 on. No
other unchosen vertex's selection-time cardinality changes at any step, so
the first step whose MCS choice can break is tightly characterized:
  - insertion: the first break can only occur in steps pos[u]+1 .. pos[v].
    Before pos[u]+1 the prefix lacks u; past pos[v] the edge touches no
    unchosen vertex.
  - deletion: only step pos[v] can be the first break. Before it, v is
    unchosen and its cardinality drop cannot beat the surviving max; after
    it, v's own cardinality no longer matters.
The window is tight for the PROBE (the first position where the ordering
diverges), but once the choice breaks, the prefix changes and the ordering
may legitimately diverge through the end of the order, so the regreedy runs
on the full suffix from the first breaking step with bucket MCS (Rose-Tarjan,
bitmask buckets, seed = popcount against the retained prefix). Often the
probe finds no break and no regreedy is needed.
"""


def _prefix_mask(order, k):
    """Bitmask of the first k vertices of the order."""
    m = 0
    for i in range(k):
        m |= 1 << order[i]
    return m


def _regreedy(order, pos, mask, n, k0):
    """Re-run bucket MCS on order[k0:], keeping order[:k0] fixed."""
    remaining = 0
    for i in range(k0, n):
        remaining |= 1 << order[i]
    if not remaining:
        return
    prefix = ((1 << n) - 1) ^ remaining
    card = [0] * n
    buckets = [0] * (n + 1)
    maxc = 0
    r = remaining
    while r:
        b = r & -r
        v = b.bit_length() - 1
        r ^= b
        c = (mask[v] & prefix).bit_count()
        card[v] = c
        buckets[c] |= b
        if c > maxc:
            maxc = c
    k = k0
    while remaining:
        while not buckets[maxc]:
            maxc -= 1
        b = buckets[maxc] & -buckets[maxc]  # smallest id in top bucket
        v = b.bit_length() - 1
        buckets[maxc] ^= b
        remaining ^= b
        order[k] = v
        pos[v] = k
        k += 1
        nb = mask[v] & remaining
        while nb:
            b = nb & -nb
            nb ^= b
            w = b.bit_length() - 1
            buckets[card[w]] ^= b
            card[w] += 1
            buckets[card[w]] |= b
            if card[w] > maxc:
                maxc = card[w]


def _first_break(order, mask, k0, k1, v):
    """Insertion repair probe. v's cardinality rose by one for every prefix
    in steps [k0, k1]; all other cardinalities are unchanged. At step k the
    old choice order[k] (cardinality c, the old max) survives iff the new
    max is still c and order[k] is the smallest id attaining it, i.e. iff
    d < c, or d == c and order[k] < v. Return the first breaking step, or
    None if the whole window survives."""
    prefix = _prefix_mask(order, k0)
    d = (mask[v] & prefix).bit_count()
    for k in range(k0, k1 + 1):
        c = (mask[order[k]] & prefix).bit_count()
        if d > c or (d == c and v < order[k]):
            return k
        prefix |= 1 << order[k]
        if (mask[v] >> order[k]) & 1:
            d += 1
    return None


def _deletion_breaks(order, mask, pv, v):
    """Deletion repair probe. Only step pv can break: v's cardinality there
    dropped by one to c, every other unchosen cardinality is unchanged (and
    was at most c + 1, with v the smallest id at the old max). The step
    breaks iff some other unchosen vertex now strictly beats v, or ties it
    with a smaller id."""
    prefix = _prefix_mask(order, pv)
    c = (mask[v] & prefix).bit_count()
    for i in range(pv + 1, len(order)):
        w = order[i]
        cw = (mask[w] & prefix).bit_count()
        if cw > c or (cw == c and w < v):
            return True
    return False


def init(graph):
    n = len(graph)
    mask = [0] * n
    for u in range(n):
        row = graph[u]
        m = 0
        for v in range(n):
            if row[v]:
                m |= 1 << v
        mask[u] = m
    order = list(range(n))
    pos = [0] * n
    _regreedy(order, pos, mask, n, 0)
    return {"n": n, "mask": mask, "order": order, "pos": pos}


def _update(edge, state, present):
    u, v = edge
    mask = state["mask"]
    if present:
        mask[u] |= 1 << v
        mask[v] |= 1 << u
    else:
        mask[u] &= ~(1 << v)
        mask[v] &= ~(1 << u)
    order = state["order"]
    pos = state["pos"]
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu
    # v is the later endpoint: the only vertex whose selection-time
    # cardinality the flip changes.
    if present:
        k = _first_break(order, mask, pu + 1, pv, v)
    else:
        k = pv if _deletion_breaks(order, mask, pv, v) else None
    if k is not None:
        _regreedy(order, pos, mask, state["n"], k)
    return state


def insert_edge(graph, edge, state):
    return _update(edge, state, True)


def delete_edge(graph, edge, state):
    return _update(edge, state, False)
