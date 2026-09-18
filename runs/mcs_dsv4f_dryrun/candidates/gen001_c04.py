"""Dynamic Maximum Cardinality Search ordering (undirected).

Offline MCS: each round pick an unchosen vertex whose number of already-chosen
neighbors (cardinality) is maximal, ties broken by lowest vertex id.

Dynamic update after flipping edge (u,v); `graph` is the post-update matrix:
Let a be the endpoint that appears earlier in the maintained ordering
(position pa), b the other (position pb > pa). For every step 0..pa-1 neither
u nor v is chosen, so changing edge (u,v) never changes any cardinality and the
greedy picks (including lowest-id tie-breaks) are identical to a fresh MCS run.
The prefix order[:pa+1] is therefore preserved exactly.

Only the suffix is recomputed: initialize cardinalities from the preserved
prefix (chosen neighbors only) and run the plain greedy to completion on the
post-update graph. This always yields a valid MCS ordering.
"""


def init(graph):
    n = len(graph)
    chosen = [False] * n
    card = [0] * n
    ordering = []
    for _ in range(n):
        best = -1
        bc = -1
        for w in range(n):
            if not chosen[w] and (card[w] > bc or
                                  (card[w] == bc and (best == -1 or w < best))):
                best = w
                bc = card[w]
        ordering.append(best)
        chosen[best] = True
        row = graph[best]
        for w in range(n):
            if row[w] == 1 and not chosen[w]:
                card[w] += 1
    return {"ordering": ordering}


def _update(graph, edge, state):
    u, v = edge
    if u == v:
        return state
    order = state["ordering"]
    n = len(graph)
    pos = {w: i for i, w in enumerate(order)}
    pa, pb = pos.get(u, -1), pos.get(v, -1)
    if pa < 0 or pb < 0:
        return state
    a, pa = (u, pa) if pa < pb else (v, pa)
    # prefix through the earlier endpoint a is identical to a fresh run.
    prefix = order[: pa + 1]
    chosen = [w in prefix for w in range(n)]
    # cardinality = number of already-chosen (prefix) neighbors.
    card = [sum(1 for x in prefix if graph[w][x] == 1) for w in range(n)]
    ordering = list(prefix)
    for _ in range(n - pa - 1):
        best = -1
        bc = -1
        for w in range(n):
            if not chosen[w] and (card[w] > bc or
                                  (card[w] == bc and (best == -1 or w < best))):
                best = w
                bc = card[w]
        ordering.append(best)
        chosen[best] = True
        row = graph[best]
        for w in range(n):
            if row[w] == 1 and not chosen[w]:
                card[w] += 1
    return {"ordering": ordering}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)