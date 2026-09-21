"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Approach: keep the MCS order pi and recompute only the suffix an edge flip
can invalidate. Insert (u,v) with pos[u] < pos[v] raises only v's
cardinality, and only from step pos[u]+1 on (during step pos[u] itself u is
not yet chosen, so v's count is unchanged there); steps 0..pos[u] stay
valid. Delete (u,v) lowers only v's cardinality; at every step before
pos[v] the chosen vertex itself is still unchosen and witnesses the old
max, so only step pos[v] can lose maximality. The suffix is rerun with a
bucket (lazy radix) MCS seeded by the untouched prefix, so work is
proportional to the suffix, not the whole graph.
"""


def _mcs_suffix(prefix, rest, adj, n):
    """Bucket MCS over `rest` with `prefix` already chosen (Rose-Tarjan)."""
    chosen = [False] * n
    for v in prefix:
        chosen[v] = True
    cnt = [0] * n
    buckets = [[] for _ in range(n + 1)]
    max_b = 0
    for v in rest:
        c = 0
        for w in adj[v]:
            if chosen[w]:
                c += 1
        cnt[v] = c
        buckets[c].append(v)
        if c > max_b:
            max_b = c
    order = []
    remaining = len(rest)
    while remaining:
        while max_b >= 0 and not buckets[max_b]:
            max_b -= 1
        v = buckets[max_b].pop()
        if chosen[v]:  # stale lazy-bucket entry
            continue
        chosen[v] = True
        remaining -= 1
        order.append(v)
        for w in adj[v]:
            if not chosen[w]:
                cnt[w] += 1
                buckets[cnt[w]].append(w)
                if cnt[w] > max_b:
                    max_b = cnt[w]
    return order


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    order = _mcs_suffix([], list(range(n)), adj, n)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    order = state["order"]
    # First step whose max can change: the earlier endpoint's step is still
    # valid (the new edge does not touch any count measured there).
    p = min(state["pos"][u], state["pos"][v]) + 1
    order[p:] = _mcs_suffix(order[:p], order[p:], adj, state["n"])
    for i in range(p, state["n"]):
        state["pos"][order[i]] = i
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    # Only the later endpoint's own step can lose maximality: at every
    # earlier step the chosen vertex itself still attains the old max.
    p = max(state["pos"][u], state["pos"][v])
    order = state["order"]
    order[p:] = _mcs_suffix(order[:p], order[p:], adj, state["n"])
    for i in range(p, state["n"]):
        state["pos"][order[i]] = i
    return state
