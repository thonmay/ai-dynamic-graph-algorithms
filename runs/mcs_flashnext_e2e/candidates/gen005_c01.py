"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Derived from the bucket-suffix parent (keep the order pi, rerun only the
suffix an edge flip can invalidate with a lazy radix bucket MCS), with two
mutations:

1. State addition: cnt_sel[w] = |N(w) intersect order[:pos[w]]|, the
   cardinality w held at its own selection step (the max at that step). It
   is kept globally correct on every operation: the suffix rerun refreshes
   it for EVERY vertex it picks (no early stop), and the fast paths only
   touch the one vertex whose selection count actually changes.
2. Insert fast path. Insert (u,v), pos[u] < pos[v], raises only v's count,
   by exactly 1, at every step in (pos[u], pos[v]); steps <= pos[u] are
   untouched and from pos[v] on v is chosen with the raised count, so the
   old order survives iff v's raised count never exceeds the chosen vertex's
   count strictly between the endpoints. Old validity gives v's old count
   <= the step max, so the order breaks exactly where v was tied for the
   max, i.e. where its new count exceeds cnt_sel[order[i]]. A carried count
   with O(1) set lookups finds the first such step in O(deg(v) + window).
   When none exists the rerun is skipped entirely; otherwise it starts at
   the first violating step (a suffix of the parent's rerun).

Delete is the parent's rule (rerun from the later endpoint's step, the only
step that can lose maximality) but routed through the same cnt_sel-
refreshing rerun so the invariant survives for later insert fast paths.

Tie-breaking is by bucket pop order (LIFO); the invariant only requires each
pick to have maximum cardinality, not a specific tie-break. The rerun's
greedy is identical to the parent's, so the produced order matches the
passing parent's order.
"""


def _rerun(order, p, adj, n, cnt_sel):
    """Bucket MCS over order[p:] with order[:p] chosen (Rose-Tarjan).

    Identical selection to the parent (same seeding order over order[p:],
    same LIFO pops, same top pointer), so the returned suffix equals the
    parent's. Also refreshes cnt_sel[w] to the count each picked vertex had
    at its own step, for every vertex in the suffix, keeping the invariant
    cnt_sel[w] = |N(w) intersect order[:pos[w]]| globally true. No early
    stop: a stale tail is what broke the prior fast-path candidates.
    """
    chosen = [False] * n
    for i in range(p):
        chosen[order[i]] = True
    cnt = [0] * n
    buckets = [[] for _ in range(n + 1)]
    max_b = 0
    for i in range(p, n):
        w = order[i]
        c = 0
        for x in adj[w]:
            if chosen[x]:
                c += 1
        cnt[w] = c
        buckets[c].append(w)
        if c > max_b:
            max_b = c
    out = []
    remaining = n - p
    while remaining:
        while max_b >= 0 and not buckets[max_b]:
            max_b -= 1
        w = buckets[max_b].pop()
        if chosen[w]:
            continue  # stale lazy-bucket entry
        chosen[w] = True
        remaining -= 1
        out.append(w)
        cnt_sel[w] = cnt[w]  # count at selection == max_b at pick
        for x in adj[w]:
            if not chosen[x]:
                cnt[x] += 1
                buckets[cnt[x]].append(x)
                if cnt[x] > max_b:
                    max_b = cnt[x]
    return out


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
    order = _rerun(list(range(n)), 0, adj, n, cnt_sel)
    pos = [0] * n
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
    # (post-insert adjacency, so u with pos pu is counted).
    c = 0
    for x in adj[v]:
        if pos[x] <= pu:
            c += 1
    i0 = None
    for i in range(pu + 1, pv):
        if c > cnt_sel[order[i]]:
            # v's raised count beats the chosen vertex's count at step i:
            # first invalid step.
            i0 = i
            break
        if order[i] in adj[v]:
            c += 1
    if i0 is None:
        # No step between the endpoints breaks: the order is still valid.
        # Only v's own selection count changed (u sits before v).
        cnt_sel[v] += 1
        return state
    suffix = _rerun(order, i0, adj, n, cnt_sel)
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
    suffix = _rerun(order, p, adj, n, state["cnt_sel"])
    order[p:] = suffix
    for i in range(p, n):
        pos[order[i]] = i
    return state
