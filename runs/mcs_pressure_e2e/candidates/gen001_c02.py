"""Dynamic MCS (undirected): maintain a valid maximum-cardinality-search ordering.

Approach: keep the ordering pi, a position array, and adjacency sets. Flipping
edge (u, v) changes the selection-time cardinality of only the later-positioned
endpoint, and only once the earlier endpoint enters the prefix. That gives an
asymmetric restart point:
- Insertion: the later endpoint's cardinality grows by one, so the first
  possibly-invalid choice is step min(pos) + 1; restart the greedy there.
- Deletion: the later endpoint's cardinality only shrinks, and it is not
  chosen at any step before its own position, so every choice strictly before
  max(pos) stays valid; restart at max(pos) itself.
Re-run bucket-based greedy MCS (Rose-Tarjan style) on the suffix only; any
max-cardinality choice is a valid MCS ordering, so no tie-break is forced.
"""


def _mcs_regreedy(adj, ordering, pos, k0):
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
        v = buckets[maxc].pop()
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
    _mcs_regreedy(adj, ordering, pos, 0)
    return {"ordering": ordering, "pos": pos, "adj": adj}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    pos = state["pos"]
    _mcs_regreedy(adj, state["ordering"], pos, min(pos[u], pos[v]) + 1)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    pos = state["pos"]
    _mcs_regreedy(adj, state["ordering"], pos, max(pos[u], pos[v]))
    return state
