"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Derived from the bucket-suffix parent: same skeleton (keep the order pi and
rerun only the suffix an edge flip can invalidate), with these mutations:

1. State addition: cnt_sel[w], the cardinality w had at its own selection
   step (|N(w) intersect order[:pos[w]]|), plus a max segment tree over
   cnt_sel indexed by position: A[i] = cnt_sel[order[i]].
2. Insert fast path (no rerun). Insert (u,v), pos[u] < pos[v], raises only
   v's count, by exactly 1, at steps in (pos[u], pos[v]); steps <= pos[u]
   are untouched and from pos[v] on v is chosen with a raised count, so the
   old order survives iff v was never tied for the max strictly between the
   endpoints (count_old(v,i) < A[i] there; old validity gives <=). A
   carried count with O(1) set lookups finds the first tie in O(window);
   no adjacency reseeding when there is none.
3. Delete fast path, O(log n). Delete (u,v), pos[u] < pos[v], lowers only
   v's count. At every step before pos[v] the chosen vertex keeps the old
   max and only v drops, so only step pos[v] can break; it stays valid when
   every later vertex's count at step pos[v] is below v's old count, and
   each such count is at most that vertex's own selection count, so one
   range-max over A[pos[v]+1:] <= cnt_sel[v]-1 certifies the whole order
   with a single point update.
4. Rerun starts at the first invalid step (first tie for insert, pos[v] for
   delete) and stops as soon as the picked set equals the old positions
   p..k with v picked: only v's adjacency differs from the old graph, v is
   chosen and u is in the prefix, so every unchosen vertex keeps its old
   count and the untouched old tail is still a valid MCS suffix. The tree
   is point-updated on [p, k]; tail entries stay correct because those
   selection counts are unchanged.

Tie-breaking is by bucket pop order (LIFO); the invariant only requires each
pick to have maximum cardinality, not a specific tie-break.
"""


def _seg_query(tree, n, l, r):
    """Max over A[l:r] (position-indexed selection counts), -1 if empty."""
    l += n
    r += n
    res = -1
    while l < r:
        if l & 1:
            if tree[l] > res:
                res = tree[l]
            l += 1
        if r & 1:
            r -= 1
            if tree[r] > res:
                res = tree[r]
        l >>= 1
        r >>= 1
    return res


def _seg_update(tree, n, i, val):
    i += n
    tree[i] = val
    i >>= 1
    while i:
        tree[i] = max(tree[2 * i], tree[2 * i + 1])
        i >>= 1


def _rerun(order, pos, p, adj, n, cnt_sel, v):
    """Bucket MCS over order[p:] with order[:p] chosen, with early stop.

    `pos` holds the OLD positions during the rerun. Stops once the picked
    set equals old positions p..k and v has been picked; the old tail
    order[k+1:] is then still a valid MCS suffix and is appended as is.
    Refreshes cnt_sel for every vertex it picks. Returns (suffix, stop).
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
            continue  # stale lazy-bucket entry
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
    cnt_sel = [0] * n
    # v = -1 is never picked, so the initial run never stops early.
    order, _ = _rerun(list(range(n)), [0] * n, 0, adj, n, cnt_sel, -1)
    pos = [0] * n
    for i, w in enumerate(order):
        pos[w] = i
    tree = [-1] * (2 * n)
    for i, w in enumerate(order):
        tree[n + i] = cnt_sel[w]
    for i in range(n - 1, 0, -1):
        tree[i] = max(tree[2 * i], tree[2 * i + 1])
    return {"n": n, "adj": adj, "order": order, "pos": pos,
            "cnt_sel": cnt_sel, "tree": tree}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    pos = state["pos"]
    order = state["order"]
    cnt_sel = state["cnt_sel"]
    tree = state["tree"]
    n = state["n"]
    if pos[u] > pos[v]:
        u, v = v, u
    pu, pv = pos[u], pos[v]
    # v's OLD count at step pu+1: new neighbors of v chosen by then, minus u
    # (u is chosen at step pu, not before it, and was not an old neighbor).
    c = -1
    for x in adj[v]:
        if pos[x] <= pu:
            c += 1
    i0 = None
    for i in range(pu + 1, pv):
        if c == cnt_sel[order[i]]:
            # v's old count ties the old max at step i: its raised count
            # exceeds it, so step i is the first invalid step.
            i0 = i
            break
        if order[i] in adj[v]:
            c += 1
    if i0 is None:
        # No step between the endpoints breaks: the order is still valid.
        # Only v's own selection count changed (u sits before v).
        cnt_sel[v] += 1
        _seg_update(tree, n, pv, cnt_sel[v])
        return state
    suffix, stop = _rerun(order, pos, i0, adj, n, cnt_sel, v)
    order[i0:] = suffix
    for i in range(i0, stop + 1):
        pos[order[i]] = i
        _seg_update(tree, n, i, cnt_sel[order[i]])
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    pos = state["pos"]
    order = state["order"]
    cnt_sel = state["cnt_sel"]
    tree = state["tree"]
    n = state["n"]
    if pos[u] > pos[v]:
        u, v = v, u
    p = pos[v]
    # Only step p can break: v's count drops to cnt_sel[v] - 1 there and
    # every other unchosen vertex keeps its count, which at step p is at
    # most its own selection count. If all later selection counts stay
    # below the old cnt_sel[v], step p is still valid and so is the order.
    if _seg_query(tree, n, p + 1, n) <= cnt_sel[v] - 1:
        cnt_sel[v] -= 1
        _seg_update(tree, n, p, cnt_sel[v])
        return state
    suffix, stop = _rerun(order, pos, p, adj, n, cnt_sel, v)
    order[p:] = suffix
    for i in range(p, stop + 1):
        pos[order[i]] = i
        _seg_update(tree, n, i, cnt_sel[order[i]])
    return state
