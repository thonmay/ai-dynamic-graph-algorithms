"""Dynamic Maximum Cardinality Search (MCS) ordering, undirected graphs.

Maintains a vertex ordering that is a valid MCS ordering of the current
graph: each vertex is chosen when its cardinality (number of already-chosen
neighbors) is maximal among the unchosen vertices (ties broken by smallest id).

Approach (fully dynamic, prefix-preserving, bitset buckets): adjacency is one
bitmask per vertex, so flipping edge (u, v) is two int ops. Let pos[u] < pos[v].
The flip changes the selection-time cardinality of no vertex except v: on
insertion v's cardinality grows by one only from step pos[u] + 1 on (u enters
the prefix then), so the prefix through pos[u] survives; on deletion v's
cardinality shrinks, which cannot invalidate any step before pos[v]: the
vertex chosen at such a step is itself an unchosen vertex whose cardinality
the deletion cannot touch, and deletion only lowers cardinalities, so the
max among the unchosen cannot drop below it. The prefix through pos[v] - 1
therefore survives. The suffix after the restart point is regreedy with
classic bucket MCS (Rose-Tarjan) using bitmask buckets: seed each suffix
vertex's cardinality as popcount(neighbors in the retained prefix), pick the
smallest id in the top bucket (lowbit), move neighbors up one bucket on
choice.
"""


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
    pos = state["pos"]
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        pu, pv = pv, pu
    # Insertion can raise the running max only after u enters the prefix;
    # deletion can break validity only at v's own selection step.
    k0 = pu + 1 if present else pv
    _regreedy(state["order"], pos, mask, state["n"], k0)
    return state


def insert_edge(graph, edge, state):
    return _update(edge, state, True)


def delete_edge(graph, edge, state):
    return _update(edge, state, False)
