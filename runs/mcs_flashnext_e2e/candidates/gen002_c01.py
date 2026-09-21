"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Derived from the heap-suffix parent with three mutations:
1. Bucket (radix) buckets replace the lazy max-heap in the suffix rerun.
2. Tighter insertion cut: rerun from pos[u] + 1 (u = earlier endpoint).
   At step pos[u] itself u is not yet chosen, so no count changes there
   and the old choice at that step stays valid.
3. Early-stop rejoin: during the rerun, stop as soon as the picked set
   equals the old prefix set and v (the endpoint whose adjacency changed)
   has been picked. Every unchosen vertex then has exactly its old count
   (only v's adjacency differs from the old graph and v is chosen), so
   the untouched tail of the old order is still a valid MCS suffix.
   For an insertion this bounds the rerun to the window between the two
   endpoints' positions in the common case: at v's own step its raised
   count strictly beats the old max, so v is picked by then and the
   picked set rejoins the old prefix there.
"""


def _rerun(order, pos, p, adj, n, v):
    """Bucket MCS over order[p:] with order[:p] chosen, with early stop.

    `pos` holds the OLD positions during the rerun. Stops once the picked
    set matches the old prefix positions p..k and v has been picked; the
    untouched old tail order[k+1:] is then still valid and is appended as
    is. Returns (new suffix, stop step k).
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
    # v = -1 is never picked, so the initial run never stops early.
    order, _ = _rerun(list(range(n)), [0] * n, 0, adj, n, -1)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    pos = state["pos"]
    order = state["order"]
    if pos[u] > pos[v]:
        u, v = v, u
    # u is the earlier endpoint. Only v's count changes, and only at
    # steps after pos[u], so the prefix through pos[u] stays valid.
    p = pos[u] + 1
    suffix, stop = _rerun(order, pos, p, adj, state["n"], v)
    order[p:] = suffix
    for i in range(p, stop + 1):
        pos[order[i]] = i
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    pos = state["pos"]
    order = state["order"]
    if pos[u] > pos[v]:
        u, v = v, u
    # Only v's count drops. At every step before pos[v] the chosen vertex
    # keeps its old count, which was the old max and is still maximal
    # (v's new count is at most old max - 1), so only step pos[v] onward
    # can change.
    p = pos[v]
    suffix, stop = _rerun(order, pos, p, adj, state["n"], v)
    order[p:] = suffix
    for i in range(p, stop + 1):
        pos[order[i]] = i
    return state
