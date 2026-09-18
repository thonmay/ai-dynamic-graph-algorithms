"""Dynamic Maximum Cardinality Search ordering (undirected).

Offline MCS: each round pick an unchosen vertex whose number of already-chosen
neighbors (cardinality) is maximal, ties broken by lowest vertex id.

Dynamic update (edge flip (u,v); graph is the post-update matrix):
Until the earlier endpoint a = argminpos(u,v) is chosen, the two graphs only
differ on (u,v), neither endpoint is chosen, so no cardinality differs and the
ordering prefix through pos(a) is identical to a fresh MCS run. Only the suffix
is rebuilt.

Refinement over a full suffix recompute: recompute step by step, and as soon as
the fresh choices match the stored ordering at a position >= pos(later endpoint)
(which guarantees BOTH u and v are already chosen, so the flipped edge no longer
affects any future cardinality and the unchanged stored suffix is still valid),
reuse the stored suffix and stop. Edges that don't disturb the MCS ordering cost
essentially just the prefix scan.
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
    pu, pv = pos.get(u, -1), pos.get(v, -1)
    if pu < 0 or pv < 0:
        return state
    if pu < pv:
        a, b, pa, pb = u, v, pu, pv
    else:
        a, b, pa, pb = v, u, pv, pu
    # prefix through the earlier endpoint a is preserved.
    prefix = order[: pa + 1]
    chosen = [w in prefix for w in range(n)]
    card = [sum(1 for x in prefix if graph[w][x] == 1) for w in range(n)]
    new = list(prefix)
    matched = True
    idx = pa + 1
    while idx < n:
        best = -1
        bc = -1
        for w in range(n):
            if not chosen[w] and (card[w] > bc or
                                  (card[w] == bc and (best == -1 or w < best))):
                best = w
                bc = card[w]
        # fresh run agrees with stored ordering here and the later endpoint b is
        # already chosen: both u and v are chosen, the flipped edge can no longer
        # change any future cardinality, so the stored suffix is still valid.
        if matched and best == order[idx] and idx >= pb:
            new.extend(order[idx:])
            break
        if best != order[idx]:
            matched = False
        new.append(best)
        chosen[best] = True
        row = graph[best]
        for w in range(n):
            if row[w] == 1 and not chosen[w]:
                card[w] += 1
        idx += 1
    return {"ordering": new}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)