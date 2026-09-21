"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Derived from the heap-suffix parent: same skeleton (keep the order pi, rerun
only the suffix an edge flip can invalidate), with three mutations:

1. Insertion no-rerun fast path, backed by stored selection counts.
   cnt_sel[w] = number of neighbors of w in order[:pos[w]], i.e. the max
   cardinality at w's own step. Insert (u,v), pos[u] < pos[v], raises only
   v's count, by exactly 1, at steps in (pos[u], pos[v]); steps <= pos[u]
   and steps >= pos[v] stay valid (at pos[v] v's raised count is still the
   max; after pos[v] only u's count could differ and u is chosen). So the
   old order survives iff v was never tied for the max at a step strictly
   between the endpoints. v's running count is carried with O(1) set
   lookups per step, so the check costs O(deg(v) + window) with no
   adjacency reseeding.
2. Tighter rerun point: on the first tie at step i0, rerun from i0 itself
   (the first invalid step), not from pos[u].
3. Early-stop rejoin in the rerun: stop once the picked set equals the old
   positions p..k and v has been picked. Only v's adjacency differs from
   the old graph, v is chosen and u is in the prefix, so every unchosen
   vertex keeps its old count and the untouched old tail is still a valid
   MCS suffix.

Tie-breaking is by bucket pop order (LIFO); the invariant only requires
each pick to have maximum cardinality, not a specific tie-break.
"""


def _rerun(order, pos, p, adj, n, cnt_sel, v):
    """Bucket MCS over order[p:] with order[:p] chosen, with early stop.

    `pos` holds the OLD positions during the rerun. Stops once the picked
    set matches old positions p..k and v has been picked; the old tail
    order[k+1:] is then still valid and is appended as is. Refreshes
    cnt_sel for every vertex it picks. Returns (new suffix, stop step k).
    """
    chosen = [False] * n
    for i in range(p):
        chosen[order[i]] = True
    cnt = [0] * n
    buckets = [[] for _ in range(n + 1)]
    top = 0
    for i in range(p, n):
        w = order[i]
        c = 0
        for x in adj[w]:
            if chosen[x]:
                c += 1
        cnt[w] = c
        buckets[c].append(w)
        if c > top:
            top = c
    picked = []
    max_pos_picked = p - 1
    v_picked = False
    remaining = n - p
    stop = n - 1
    while remaining:
        while not buckets[top]:
            top -= 1
        w = buckets[top].pop()
        if chosen[w] or cnt[w] != top:
            continue  # stale bucket entry
        chosen[w] = True
        remaining -= 1
        picked.append(w)
        cnt_sel[w] = top
        if pos[w] > max_pos_picked:
            max_pos_picked = pos[w]
        if w == v:
            v_picked = True
        k = p + len(picked) - 1
        if remaining and v_picked and max_pos_picked <= k:
            # Picked set == old positions p..k and v is chosen: every
            # unchosen vertex keeps its old count, so the old tail holds.
            stop = k
            picked.extend(order[k + 1:])
            break
        for x in adj[w]:
            if not chosen[x]:
                cnt[x] += 1
                buckets[cnt[x]].append(x)
                if cnt[x] > top:
                    top = cnt[x]
    return picked, stop


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
    cnt_sel = [0] * n
    # v = -1 is never picked, so the initial run never stops early.
    order, _ = _rerun(order, [0] * n, 0, adj, n, cnt_sel, -1)
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
    # v is the later endpoint. Its count rises by 1 at every step in
    # (pos[u], pos[v]); the old order breaks exactly where v was tied for
    # the max, i.e. where its NEW count equals cnt_sel[order[i]] + 1.
    c = 0
    for x in adj[v]:
        if pos[x] <= pos[u]:
            c += 1
    i0 = None
    for i in range(pos[u] + 1, pos[v]):
        if c == cnt_sel[order[i]] + 1:
            i0 = i
            break
        if order[i] in adj[v]:
            c += 1
    if i0 is None:
        # No step between the endpoints breaks: the order is still valid.
        # Only v's own selection count changed (u sits before v).
        cnt_sel[v] += 1
        return state
    suffix, stop = _rerun(order, pos, i0, adj, n, cnt_sel, v)
    order[i0:] = suffix
    for i in range(i0, stop + 1):
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
    if pos[u] > pos[v]:
        u, v = v, u
    # Only v's count drops. At every step before pos[v] the chosen vertex
    # itself keeps the old max, and after pos[v] only u's count could
    # differ while u is already chosen, so only step pos[v] onward can
    # change. The rerun's early stop exits at once when v stays maximal.
    p = pos[v]
    suffix, stop = _rerun(order, pos, p, adj, n, state["cnt_sel"], v)
    order[p:] = suffix
    for i in range(p, stop + 1):
        pos[order[i]] = i
    return state
