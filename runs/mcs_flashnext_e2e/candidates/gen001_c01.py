"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Approach: maintain the MCS selection order pi. An edge flip (u,v) changes
cardinalities only relative to the earlier endpoint's position, so it can
only invalidate a contiguous range of steps between the two endpoints'
positions (insertion: steps [pos_min, pos_max) where the later endpoint was
tied for max; deletion: step pos_max where the later endpoint's count drops
below the max). Prefix steps before that range stay valid because the
vertex selected at each such step keeps its old count, which still equals
the max. So we re-run the greedy selection on the suffix starting at the
first affected position, seeded with the unchanged prefix, using a lazy
max-heap (ties broken by smallest id).
"""

import heapq


def _greedy(prefix, candidates, adj, n):
    """MCS greedy on `candidates` given `prefix` already chosen.

    Picks repeatedly the candidate with max count of chosen neighbors
    (smallest id on ties), updating neighbor counts incrementally.
    """
    chosen = [False] * n
    for v in prefix:
        chosen[v] = True
    count = [0] * n
    heap = []
    for v in candidates:
        c = 0
        for w in adj[v]:
            if chosen[w]:
                c += 1
        count[v] = c
        heap.append((-c, v))
    heapq.heapify(heap)
    result = []
    remaining = len(candidates)
    while remaining:
        neg_c, v = heapq.heappop(heap)
        if chosen[v] or -neg_c != count[v]:
            continue  # stale heap entry
        chosen[v] = True
        remaining -= 1
        result.append(v)
        for w in adj[v]:
            if not chosen[w]:
                count[w] += 1
                heapq.heappush(heap, (-count[w], w))
    return result


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    order = _greedy([], list(range(n)), adj, n)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    # Cardinality of the later endpoint rises at every step from the
    # earlier endpoint's position on; recompute that suffix.
    p = min(state["pos"][u], state["pos"][v])
    order = state["order"]
    order[p:] = _greedy(order[:p], order[p:], adj, state["n"])
    for i in range(p, state["n"]):
        state["pos"][order[i]] = i
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    # Only the later endpoint's own step can lose maximality (its count
    # drops by one); all earlier steps keep their selected vertex at the
    # old max. Recompute from that step on.
    p = max(state["pos"][u], state["pos"][v])
    order = state["order"]
    order[p:] = _greedy(order[:p], order[p:], adj, state["n"])
    for i in range(p, state["n"]):
        state["pos"][order[i]] = i
    return state
