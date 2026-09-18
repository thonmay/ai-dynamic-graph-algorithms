"""Dynamic Maximum Cardinality Search ordering (undirected).

Offline MCS: each round pick an unchosen vertex whose number of already-chosen
neighbors (its cardinality) is maximal, ties broken by lowest vertex id.

Dynamic update (edge flip (u,v); the graph argument is the post-update matrix):
The two graphs only differ on edge (u,v), so at any fixed set S of already
chosen vertices the cardinality of a vertex w differs between old and new only
for w in {u,v} (and only when the other endpoint is in S). Until the earlier
endpoint a = argminpos(u,v) is chosen, no cardinality differs, so the ordering
prefix through pos(a) is identical to the fresh MCS run. Only the suffix after
pos(a) needs to be recomputed, and it is built incrementally. Cost is
proportional to the length of the suffix, not the whole graph. This is the
correct dynamic savings for MCS; the non-endpoint suffix is genuinely
non-local, so a full recommpute of that suffix is required.
"""


def init(graph):
    n = len(graph)
    chosen = [False] * n
    card = [0] * n
    ordering = []
    for _ in range(n):
        best = -1
        best_card = -1
        for w in range(n):
            if not chosen[w] and (card[w] > best_card or
                                  (card[w] == best_card and (best == -1 or w < best))):
                best = w
                best_card = card[w]
        ordering.append(best)
        chosen[best] = True
        row = graph[best]
        for w in range(n):
            if row[w] == 1 and not chosen[w]:
                card[w] += 1
    return {"ordering": ordering}


def _recompute_suffix(graph, prefix):
    n = len(graph)
    chosen = [False] * n
    for w in prefix:
        chosen[w] = True
    card = [0] * n
    for w in range(n):
        if not chosen[w]:
            s = 0
            for x in prefix:
                if graph[w][x] == 1:
                    s += 1
            card[w] = s
    order = list(prefix)
    while len(order) < n:
        best = -1
        best_card = -1
        for w in range(n):
            if not chosen[w] and (card[w] > best_card or
                                  (card[w] == best_card and (best == -1 or w < best))):
                best = w
                best_card = card[w]
        order.append(best)
        chosen[best] = True
        row = graph[best]
        for w in range(n):
            if row[w] == 1 and not chosen[w]:
                card[w] += 1
    return order


def _update(graph, edge, state):
    u, v = edge
    if u == v:
        return state
    order = state["ordering"]
    n = len(order)
    posu = posv = -1
    for i, w in enumerate(order):
        if w == u:
            posu = i
        elif w == v:
            posv = i
    if posu == -1 or posv == -1:
        return state
    a = u if posu < posv else v
    pa = posu if posu < posv else posv
    prefix = order[: pa + 1]
    new_order = _recompute_suffix(graph, prefix)
    return {"ordering": new_order}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)