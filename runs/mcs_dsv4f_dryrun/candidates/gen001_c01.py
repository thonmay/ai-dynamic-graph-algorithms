"""Dynamic Maximum Cardinality Search ordering (undirected).

Offline MCS greedily picks, each round, an unchosen vertex with the maximum
number of already-chosen neighbors (ties broken by lowest vertex id).

Dynamic update (edge flip (u,v), graph arg is already the post-update matrix):
An edge changes the cardinality of a vertex only once one of its endpoints is
chosen. In the current ordering, until BOTH u and v are chosen (which cannot
happen before the earlier endpoint a = argmin pos of {u,v} is chosen), the
unchosen set is never a neighbor-sensitive pair, so every step up to and
including pos(a) selects exactly the same vertex as in the new graph. Hence
that prefix is unchanged; only the suffix after pos(a) must be recomputed.
This is a genuinely dynamic improvement: the cost of a flip is proportional to
the remaining suffix, not the whole graph.
"""


def init(graph):
    n = len(graph)
    chosen = set()
    card = {v: 0 for v in range(n)}
    ordering = []
    for _ in range(n):
        unchosen = [u for u in range(n) if u not in chosen]
        max_card = max(card[u] for u in unchosen)
        v = min(u for u in unchosen if card[u] == max_card)
        ordering.append(v)
        chosen.add(v)
        for u in range(n):
            if graph[v][u] == 1 and u not in chosen:
                card[u] += 1
    return {"ordering": ordering}


def _recompute_suffix(graph, prefix):
    n = len(graph)
    chosen = set(prefix)
    card = {}
    for w in range(n):
        if w not in chosen:
            card[w] = sum(1 for x in chosen if graph[w][x] == 1)
    order = list(prefix)
    while len(order) < n:
        unchosen = [u for u in range(n) if u not in chosen]
        max_card = max(card[u] for u in unchosen)
        v = min(u for u in unchosen if card[u] == max_card)
        order.append(v)
        chosen.add(v)
        for u in range(n):
            if graph[v][u] == 1 and u not in chosen:
                card[u] += 1
    return order


def _update(graph, edge, state):
    u, v = edge
    if u == v:
        return state
    order = state["ordering"]
    pos = {w: i for i, w in enumerate(order)}
    a = u if pos[u] < pos[v] else v
    prefix = order[: pos[a] + 1]
    order = _recompute_suffix(graph, prefix)
    return {"ordering": order}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)