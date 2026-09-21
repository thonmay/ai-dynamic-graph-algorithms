"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Derived from the heap-suffix parent (keep the order pi, rerun the greedy
selection on the suffix an edge flip can invalidate), with three mutations:

1. Lazy radix buckets instead of a max-heap. Selection counts only rise
   during a run, so a top pointer over count-keyed lists gives O(1) max
   picks: the rerun costs O(suffix + edges) instead of the parent's
   O((suffix + edges) log n). Ties break by bucket pop order (LIFO); the
   invariant only requires a maximum-cardinality pick.
2. Tighter insertion start point. For insert (u,v) with pos[u] < pos[v],
   every step up to pos[u] inclusive stays valid: v gains its first new
   chosen neighbor only at step pos[u]+1, and no other unchosen count
   changes before then (u and v are both absent from every prefix ending
   at or before pos[u]). So the rerun starts at pos[u]+1, not pos[u].
   When the endpoints are adjacent in the order the window between them
   is empty and the order survives untouched: v's own step only raises
   its already-max count, and later steps see identical chosen sets with
   unchanged counts for every unchosen vertex.
3. No O(n) scratch arrays per update. Prefix membership is the position
   test pos[x] < p against the still-old positions (pos is a permutation
   and the prefix is exactly order[:p]), and newly picked vertices go
   into a set, so a small-suffix update never touches the untouched
   prefix.
"""


def _greedy(p, order, pos, adj, n):
    """MCS greedy on order[p:] with order[:p] already chosen.

    `pos` still holds the OLD positions (the caller rewrites them after
    the run), which is exactly the prefix-membership oracle needed here:
    x is chosen before step p iff pos[x] < p. Counts only increase during
    the run, so lazy count-keyed buckets with a top pointer always expose
    a live maximum. Returns the new suffix.
    """
    cnt = {}
    buckets = {}
    top = 0
    for i in range(p, n):
        w = order[i]
        c = 0
        for x in adj[w]:
            if pos[x] < p:
                c += 1
        cnt[w] = c
        buckets.setdefault(c, []).append(w)
        if c > top:
            top = c
    picked = set()
    suffix = []
    remaining = n - p
    while remaining:
        while not buckets.get(top):
            top -= 1
        w = buckets[top].pop()
        if w in picked or cnt[w] != top:
            continue  # stale lazy-bucket entry
        picked.add(w)
        remaining -= 1
        suffix.append(w)
        for x in adj[w]:
            if pos[x] >= p and x not in picked:
                c = cnt[x] + 1
                cnt[x] = c
                buckets.setdefault(c, []).append(x)
                if c > top:
                    top = c
    return suffix


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    order = list(range(n))
    # pos is read only as the prefix oracle pos[x] < p; with p = 0 the
    # test is false for any non-negative filler, so these zeros are safe.
    pos = [0] * n
    order = _greedy(0, order, pos, adj, n)
    for i, w in enumerate(order):
        pos[w] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    pos = state["pos"]
    order = state["order"]
    n = state["n"]
    if pos[u] > pos[v]:
        u, v = v, u
    p = pos[u] + 1
    if p == pos[v]:
        # Adjacent in the order: no step between the endpoints exists and
        # neither endpoint's own step loses maximality (see header).
        return state
    order[p:] = _greedy(p, order, pos, adj, n)
    for i in range(p, n):
        pos[order[i]] = i
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    pos = state["pos"]
    order = state["order"]
    n = state["n"]
    # Only the later endpoint's own step can lose maximality: its count
    # drops by one there; every earlier step keeps its chosen vertex as an
    # untouched max witness (the flip touches only u and v, and neither is
    # in that step's prefix with a changed contribution to the chosen
    # vertex); if step p survives, later steps see identical chosen sets
    # with unchanged counts. Rerun from p.
    p = max(pos[u], pos[v])
    order[p:] = _greedy(p, order, pos, adj, n)
    for i in range(p, n):
        pos[order[i]] = i
    return state
