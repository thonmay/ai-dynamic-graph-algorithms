# dynamic_mcs (undirected): maintain a Maximal Cardinality Search ordering.
#
# MCS greedily picks, each round, an unchosen vertex with the maximum number of
# already-chosen neighbours (ties broken by lowest vertex id).
#
# Dynamic update: a flipped edge (u, v) can only change the cardinality of a
# vertex once one endpoint of that edge is chosen. Both u and v stay unchosen
# through every prefix that ends before the earlier of the two is picked, so
# every greedy decision in that prefix is identical to the offline run. Only the
# suffix after the earlier endpoint is recomputed (from the preserved prefix).
#
# State: {"ordering": list[int]} -- a valid MCS ordering of the current graph.
#
# The suffix rebuild uses cardinality buckets instead of a full max-scan: cards
# of unchosen vertices are stored by value, the running max is tracked, and a
# flip only adjusts the cards of the freshly chosen vertex's unchosen neighbours.


def _full_mcs(graph):
    """Offline MCS ordering from scratch (tie-break: lowest vertex id)."""
    n = len(graph)
    ordering = []
    card = [0] * n
    chosen = [False] * n
    for _ in range(n):
        best = -1
        best_v = -1
        for v in range(n):
            if not chosen[v]:
                if card[v] > best or (card[v] == best and (best_v == -1 or v < best_v)):
                    best = card[v]
                    best_v = v
        chosen[best_v] = True
        ordering.append(best_v)
        for w in range(n):
            if graph[best_v][w] and not chosen[w]:
                card[w] += 1
    return ordering


def _rebuild_suffix(graph, prefix):
    """Rebuild ordering[prefix:] greedily, treating `prefix` as already chosen.

    Cardinalities of unchosen vertices are kept in buckets keyed by card value;
    `maxc` is the current maximum card among unchosen vertices. Choosing a vertex
    only ever increases its neighbours' cards, so maxc is monotone non-decreasing.
    """
    n = len(graph)
    chosen = [False] * n
    for w in prefix:
        chosen[w] = True
    order = list(prefix)

    card = [0] * n
    buckets = {}
    maxc = 0
    for v in range(n):
        if not chosen[v]:
            c = 0
            for w in prefix:
                if graph[v][w]:
                    c += 1
            card[v] = c
            buckets.setdefault(c, set()).add(v)
            if c > maxc:
                maxc = c

    while len(order) < n:
        cands = buckets.get(maxc, set())
        # maxc must be non-empty while unchosen vertices remain, but re-scan
        # defensively if the bucket is somehow empty.
        while not cands and maxc >= 0:
            maxc -= 1
            cands = buckets.get(maxc, set())
        v = min(cands)
        cands.remove(v)
        if not cands:
            del buckets[maxc]
        order.append(v)
        chosen[v] = True
        for w in range(n):
            if graph[v][w] and not chosen[w]:
                old = card[w]
                buckets[old].remove(w)
                if not buckets[old]:
                    del buckets[old]
                card[w] = old + 1
                buckets.setdefault(old + 1, set()).add(w)
                if old + 1 > maxc:
                    maxc = old + 1
    return order


def init(graph):
    if not graph:
        return {"ordering": []}
    return {"ordering": _full_mcs(graph)}


def _update(graph, edge, state):
    u, v = edge
    if u == v:
        return state
    ordering = state["ordering"]
    if len(ordering) <= 1:
        return state
    pos = {w: i for i, w in enumerate(ordering)}
    a = u if pos[u] < pos[v] else v
    prefix = ordering[: pos[a] + 1]
    return {"ordering": _rebuild_suffix(graph, prefix)}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)