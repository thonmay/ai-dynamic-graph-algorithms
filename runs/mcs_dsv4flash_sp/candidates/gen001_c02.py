# dynamic_mcs (undirected): maintain a Maximal Cardinality Search ordering.
#
# MCS greedily picks, at each round, an unchosen vertex whose number of already
# chosen neighbours is maximal (ties broken toward the lowest vertex id).
#
# Decrementally/incrementally dynamic update. The maintained state is just the
# current MCS ordering. When edge (u, v) flips, let a be the earlier of the two
# endpoints in the current ordering and b the later. The flip only ever changes
# the cardinality of b: edge (u,v) contributes to b's count of chosen neighbours
# exactly for the prefixes in which a is already chosen, and b, being the later
# endpoint, is still unchosen throughout [pos(a), pos(b)]. Every greedy choice
# at a position before pos(a) therefore replays identically to the offline run.
# So we preserve the prefix ending at a and rebuild only the suffix, replaying
# MCS greedily from that preserved prefix.
#
# State: {"ordering": list[int]} -- a valid MCS ordering of the current graph.
#
# The suffix rebuild keeps cardinalities of unchosen vertices in buckets keyed
# by card value; `maxc` is the running maximum card among unchosen vertices.
# Choosing a vertex only raises its neighbours' cards, so maxc is monotone
# non-decreasing and stepped only downward defensively when a bucket empties.


def _offline_mcs(graph):
    """Offline MCS ordering from scratch (tie-break: lowest vertex id)."""
    n = len(graph)
    card = [0] * n
    chosen = [False] * n
    ordering = []
    for _ in range(n):
        best, best_v = -1, -1
        for v in range(n):
            if not chosen[v] and (card[v] > best or (card[v] == best and best_v == -1)):
                best, best_v = card[v], v
        chosen[best_v] = True
        ordering.append(best_v)
        for w in range(n):
            if graph[best_v][w] and not chosen[w]:
                card[w] += 1
    return ordering


def _continue_mcs(graph, prefix):
    """Replay MCS greedily continuing from a fixed prefix of chosen vertices.

    Returns the full ordering. `prefix` must be a valid MCS prefix: it agrees
    with the offline greedy choices for its generation, so the suffix is
    recomputed only as far as the flip actually affects it.
    """
    n = len(graph)
    order = list(prefix)
    chosen = [False] * n
    for w in prefix:
        chosen[w] = True

    card = [0] * n
    buckets = {}
    maxc = 0
    for v in range(n):
        if chosen[v]:
            continue
        c = 0
        for w in prefix:
            if graph[v][w]:
                c += 1
        card[v] = c
        buckets.setdefault(c, set()).add(v)
        if c > maxc:
            maxc = c

    while len(order) < n:
        cands = buckets.get(maxc)
        while (cands is None or not cands) and maxc >= 0:
            maxc -= 1
            cands = buckets.get(maxc)
        v = min(cands)
        cands.remove(v)
        if not cands:
            del buckets[maxc]
        order.append(v)
        chosen[v] = True
        for w in range(n):
            if graph[v][w] and not chosen[w]:
                old = card[w]
                b = buckets.get(old)
                b.discard(w)
                if not b:
                    del buckets[old]
                new = old + 1
                card[w] = new
                buckets.setdefault(new, set()).add(w)
                if new > maxc:
                    maxc = new
    return order


def init(graph):
    if not graph:
        return {"ordering": []}
    return {"ordering": _offline_mcs(graph)}


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
    return {"ordering": _continue_mcs(graph, prefix)}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)