"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Approach: keep the MCS order pi and rerun the greedy only over the suffix an
edge flip can invalidate. Counts at step k are measured against vertices
chosen in steps < k, so flipping (u,v) with pos[u] < pos[v] shifts only v's
count, and only at steps k > pos[u].
- Insert: at every step k <= pos[u] no count changes at all, so the prefix
  through pos[u] stays valid; rerun from pos[u] + 1.
- Delete: at every step k < pos[v] the chosen vertex x keeps its old count,
  which was the old max, and v (the only vertex whose count drops) had
  old-count <= old max, so its new count <= old max - 1 < x's count; only
  step pos[v] can lose maximality; rerun from pos[v].
The suffix rerun is bucket MCS (Rose-Tarjan) seeded with the untouched
prefix, so work is proportional to the suffix, not the whole graph.
"""


def _mcs_bucket(prefix, rest, adj, n):
    """MCS over `rest` with `prefix` already chosen; any max-count pick."""
    in_prefix = [False] * n
    for v in prefix:
        in_prefix[v] = True
    chosen = list(in_prefix)
    cnt = [0] * n
    buckets = [[] for _ in range(n + 1)]
    top = 0
    for v in rest:
        c = 0
        for w in adj[v]:
            if in_prefix[w]:
                c += 1
        cnt[v] = c
        buckets[c].append(v)
        if c > top:
            top = c
    out = []
    left = len(rest)
    while left:
        while not buckets[top]:
            top -= 1
        v = buckets[top].pop()
        if chosen[v]:  # stale entry from a lazy count bump
            continue
        chosen[v] = True
        left -= 1
        out.append(v)
        for w in adj[v]:
            if not chosen[w]:
                cnt[w] += 1
                buckets[cnt[w]].append(w)
                if cnt[w] > top:
                    top = cnt[w]
    return out


def _rerun_from(p, state):
    """Recompute the order suffix starting at position p."""
    order = state["order"]
    n = state["n"]
    order[p:] = _mcs_bucket(order[:p], order[p:], state["adj"], n)
    pos = state["pos"]
    for i in range(p, n):
        pos[order[i]] = i


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    order = _mcs_bucket([], list(range(n)), adj, n)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    # Earlier endpoint's own step is still valid; first at-risk step is next.
    p = min(state["pos"][u], state["pos"][v]) + 1
    _rerun_from(p, state)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    # Only the later endpoint's own step can lose maximality.
    p = max(state["pos"][u], state["pos"][v])
    _rerun_from(p, state)
    return state
