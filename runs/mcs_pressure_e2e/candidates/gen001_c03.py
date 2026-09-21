"""Dynamic Maximum Cardinality Search (MCS) ordering, undirected graphs.

Maintains a vertex ordering that is a valid MCS ordering of the current
graph: each vertex is chosen when its cardinality (number of already-chosen
neighbors) is maximal among the unchosen vertices (ties broken arbitrarily).

Approach (fully dynamic, prefix-preserving): on a flip of edge (u, v), let
p = min(pos[u], pos[v]) in the maintained order. For every step i <= p the
already-chosen prefix contains neither u nor v, so the flipped edge cannot
contribute to any unchosen vertex's cardinality at that step; the old prefix
order[0..p] therefore stays a valid MCS prefix. Only the suffix after the
earlier endpoint is regenerated, using classic bucket MCS seeded with
cardinalities counted against the retained prefix. Adjacency is kept as
neighbor sets in the state, synced in O(1) per flip, so no matrix rescans.
"""


def _bucket_mcs(n, adj, chosen, cards):
    """Greedily choose all unchosen vertices, max cardinality first."""
    buckets = [set() for _ in range(n + 1)]
    max_c = 0
    remaining = 0
    for v in range(n):
        if not chosen[v]:
            buckets[cards[v]].add(v)
            remaining += 1
            if cards[v] > max_c:
                max_c = cards[v]
    order = []
    while remaining:
        while not buckets[max_c]:
            max_c -= 1
        v = buckets[max_c].pop()
        chosen[v] = True
        order.append(v)
        remaining -= 1
        for w in adj[v]:
            if not chosen[w]:
                buckets[cards[w]].remove(w)
                cards[w] += 1
                buckets[cards[w]].add(w)
                if cards[w] > max_c:
                    max_c = cards[w]
    return order


def _make_state(n, adj, order):
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos}


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    chosen = [False] * n
    cards = [0] * n
    return _make_state(n, adj, _bucket_mcs(n, adj, chosen, cards))


def _update(edge, state, present):
    u, v = edge
    n = state["n"]
    adj = state["adj"]
    if present:
        adj[u].add(v)
        adj[v].add(u)
    else:
        adj[u].discard(v)
        adj[v].discard(u)

    order = state["order"]
    pos = state["pos"]
    keep = min(pos[u], pos[v]) + 1  # provably still-valid MCS prefix
    prefix = order[:keep]

    chosen = [False] * n
    for x in prefix:
        chosen[x] = True
    cards = [0] * n
    for w in range(n):
        if not chosen[w]:
            c = 0
            for y in adj[w]:
                if chosen[y]:
                    c += 1
            cards[w] = c

    suffix = _bucket_mcs(n, adj, chosen, cards)
    return _make_state(n, adj, prefix + suffix)


def insert_edge(graph, edge, state):
    return _update(edge, state, True)


def delete_edge(graph, edge, state):
    return _update(edge, state, False)
