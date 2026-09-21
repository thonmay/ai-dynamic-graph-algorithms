"""Dynamic MCS (undirected): maintain a valid maximum-cardinality-search ordering.

Approach: keep the ordering pi, a position array, and adjacency sets. Flipping
edge (u, v) only changes the selection-time cardinality of the later-positioned
endpoint, and only at steps strictly between the two endpoints' positions, so
the prefix through min(pos[u], pos[v]) is still a valid MCS prefix. We re-run
bucket-based greedy MCS (Rose-Tarjan style) on the suffix only; any
max-cardinality choice is a valid MCS ordering, so no tie-break is forced.
"""


def _mcs_repair(adj, ordering, pos, k0):
    """Re-run greedy MCS on ordering[k0:], keeping ordering[:k0] fixed."""
    n = len(ordering)
    in_prefix = [False] * n
    for w in ordering[:k0]:
        in_prefix[w] = True
    live = [False] * n
    card = [0] * n
    buckets = [set() for _ in range(n + 1)]
    for w in ordering[k0:]:
        live[w] = True
        c = sum(1 for x in adj[w] if in_prefix[x])
        card[w] = c
        buckets[c].add(w)
    maxc = max((card[w] for w in ordering[k0:]), default=0)
    for i in range(k0, n):
        while not buckets[maxc]:
            maxc -= 1
        v = min(buckets[maxc])
        buckets[maxc].remove(v)
        live[v] = False
        ordering[i] = v
        pos[v] = i
        for w in adj[v]:
            if live[w]:
                buckets[card[w]].remove(w)
                card[w] += 1
                buckets[card[w]].add(w)
                if card[w] > maxc:
                    maxc = card[w]


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        for v in range(n):
            if graph[u][v]:
                adj[u].add(v)
    ordering = list(range(n))
    pos = list(range(n))
    _mcs_repair(adj, ordering, pos, 0)
    return {"ordering": ordering, "pos": pos, "adj": adj}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    pos = state["pos"]
    _mcs_repair(adj, state["ordering"], pos, min(pos[u], pos[v]) + 1)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    pos = state["pos"]
    _mcs_repair(adj, state["ordering"], pos, min(pos[u], pos[v]) + 1)
    return state
