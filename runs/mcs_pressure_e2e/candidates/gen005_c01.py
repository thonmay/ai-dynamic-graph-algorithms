"""Dynamic Maximum Cardinality Search (MCS) ordering, undirected graphs.

Maintains a vertex ordering that is a valid MCS ordering of the current
graph: each vertex is chosen when its cardinality (number of already-chosen
neighbors) is maximal among the unchosen vertices (ties broken by smallest id).

Derived from the parent (bitmask adjacency + tight affected window + bucket
MCS regreedy). Mutation: the state additionally carries sel_card[v], the
cardinality of v at its own selection step in the maintained order. Because a
flip of edge (u, v) with pos[u] < pos[v] changes sel_card only for v (v's
selection prefix contains u; u's does not contain v; every other vertex is not
incident), we can maintain sel_card incrementally with a single +/-1 per
update. In the old valid order the max cardinality at step k equals
sel_card[order[k]], so the repair probes read the old max in O(1) instead of a
popcount per step; the probe now walks the window with an array read plus one
incremental bit test per step. The regreedy still runs on the full suffix from
the first breaking step: the affected window is tight for the probe, but during
repair a vertex from beyond the window can legitimately become the MCS choice
inside it (its cardinality rises against the permuted prefix), so the regreedy
must be allowed to pull it in.
"""


def _prefix_mask(order, k):
    """Bitmask of the first k vertices of the order."""
    m = 0
    for i in range(k):
        m |= 1 << order[i]
    return m


def _regreedy(order, pos, sel_card, mask, n, k0):
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
        sel_card[v] = maxc
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


def _first_break(order, mask, sel_card, k0, k1, v):
    """Insertion repair probe. v's cardinality rose by one for every prefix
    in steps [k0, k1]; all other cardinalities are unchanged. At step k the
    old max is sel_card[order[k]] (the old choice's selection-time
    cardinality), and the old choice survives iff the new max is still that
    value and order[k] is the smallest id attaining it, i.e. iff d < c, or
    d == c and order[k] < v. d is v's new cardinality against the running
    prefix, tracked with one bit test per step. Return the first breaking
    step, or None if the whole window survives."""
    prefix = _prefix_mask(order, k0)
    d = (mask[v] & prefix).bit_count()
    for k in range(k0, k1 + 1):
        c = sel_card[order[k]]
        if d > c or (d == c and v < order[k]):
            return k
        prefix |= 1 << order[k]
        if (mask[v] >> order[k]) & 1:
            d += 1
    return None


def _deletion_breaks(order, mask, sel_card, pv, v):
    """Deletion repair probe. Only step pv can break: v's cardinality there
    dropped by one to c = sel_card[v], every other unchosen cardinality is
    unchanged (and was at most c + 1, with v the smallest id at the old max).
    The step breaks iff some other unchosen vertex now strictly beats v, or
    ties it with a smaller id."""
    prefix = _prefix_mask(order, pv)
    c = sel_card[v]
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
    sel_card = [0] * n
    _regreedy(order, pos, sel_card, mask, n, 0)
    return {"n": n, "mask": mask, "order": order, "pos": pos,
            "sel_card": sel_card}


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
    sel_card = state["sel_card"]
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu
    # v is the later endpoint: the only vertex whose selection-time
    # cardinality the flip changes, so sel_card needs a single +/-1 here.
    if present:
        sel_card[v] += 1
        k = _first_break(order, mask, sel_card, pu + 1, pv, v)
    else:
        sel_card[v] -= 1
        k = pv if _deletion_breaks(order, mask, sel_card, pv, v) else None
    if k is not None:
        _regreedy(order, pos, sel_card, mask, state["n"], k)
    return state


def insert_edge(graph, edge, state):
    return _update(edge, state, True)


def delete_edge(graph, edge, state):
    return _update(edge, state, False)
