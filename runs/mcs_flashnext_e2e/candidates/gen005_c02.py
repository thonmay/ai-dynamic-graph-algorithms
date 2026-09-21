"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Derived from the heap-suffix parent (keep the order pi, rerun the greedy
selection on the suffix an edge flip can invalidate), with three mutations:

1. Lazy count-keyed buckets instead of a max-heap inside the rerun. Selection
   counts only rise during a run, so a top pointer over count-keyed lists
   gives O(1) max picks: the rerun costs O(suffix + edges) instead of the
   parent's O((suffix + edges) log n). Ties break by bucket pop order (LIFO);
   the invariant only requires a maximum-cardinality pick, not a fixed
   tie-break.
2. Scratch-free rerun. Prefix membership is the position test pos[x] < p
   against the still-old positions (pos is a permutation and the prefix is
   exactly order[:p]), and newly picked vertices go into a set, so a
   small-suffix update never writes an O(n) array over the untouched prefix.
3. Insert fast path with a cnt_sel witness. cnt_sel[w] = |N(w) & order[:pos[w]]|
   is the count w held at its own selection step (the max there), kept globally
   correct: the rerun refreshes it for every vertex it picks, and the fast path
   only touches the one vertex whose selection count changes. Insert (u,v) with
   pos[u] < pos[v] raises only v's count, by exactly 1, at every step in
   (pos[u], pos[v]); steps <= pos[u] are untouched. A carried count with O(1)
   set lookups finds the first step i in (pos[u], pos[v]) where v's raised count
   exceeds cnt_sel[order[i]] (v was tied for the max there, so the old pick
   loses maximality). If none exists the order survives untouched and only
   cnt_sel[v] += 1; otherwise the rerun starts at that first violating step (a
   suffix of the parent's rerun, and of gen004's pos[u]+1 start).

Delete keeps the parent's rule (rerun from the later endpoint's step, the only
step that can lose maximality) routed through the same cnt_sel-refreshing
rerun so the witness stays valid for later insert fast paths.
"""


def _rerun(order, p, pos, adj, n, cnt_sel):
    """MCS greedy on order[p:] with order[:p] already chosen.

    `pos` still holds the OLD positions (the caller rewrites them after the
    run), which is exactly the prefix-membership oracle needed here: x is
    chosen before step p iff pos[x] < p. Counts only increase during the run,
    so lazy count-keyed buckets with a top pointer always expose a live
    maximum. Refreshes cnt_sel[w] to the count each picked vertex had at its
    own step, for every vertex in the suffix, keeping the invariant
    cnt_sel[w] = |N(w) & order[:pos[w]]| globally true. Returns the new suffix.
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
        cnt_sel[w] = cnt[w]  # count at selection == max at this step
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
    cnt_sel = [0] * n
    # pos is read only as the prefix oracle pos[x] < p; with p = 0 the test is
    # false for any non-negative filler, so these zeros are a safe placeholder.
    pos = [0] * n
    order = _rerun(list(range(n)), 0, pos, adj, n, cnt_sel)
    for i, w in enumerate(order):
        pos[w] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos, "cnt_sel": cnt_sel}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    pos = state["pos"]
    order = state["order"]
    cnt_sel = state["cnt_sel"]
    n = state["n"]
    if pos[u] > pos[v]:
        u, v = v, u
    pu, pv = pos[u], pos[v]
    # v's NEW count at step pu+1: neighbors of v already chosen by then
    # (post-insert adjacency, so u at position pu is counted).
    c = 0
    for x in adj[v]:
        if pos[x] <= pu:
            c += 1
    i0 = None
    for i in range(pu + 1, pv):
        if c > cnt_sel[order[i]]:
            # v's raised count beats the chosen vertex's count at step i:
            # the old pick at i is no longer maximal. First invalid step.
            i0 = i
            break
        if order[i] in adj[v]:
            c += 1
    if i0 is None:
        # No step between the endpoints breaks: the order is still valid.
        # Only v's own selection count changed (u now sits before v).
        cnt_sel[v] += 1
        return state
    suffix = _rerun(order, i0, pos, adj, n, cnt_sel)
    order[i0:] = suffix
    for i in range(i0, n):
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
    # Only the later endpoint's own step can lose maximality: its count drops
    # by one there; every earlier step keeps its chosen vertex as an untouched
    # max witness. Rerun from that step, refreshing cnt_sel on the suffix.
    p = max(pos[u], pos[v])
    suffix = _rerun(order, p, pos, adj, n, state["cnt_sel"])
    order[p:] = suffix
    for i in range(p, n):
        pos[order[i]] = i
    return state
