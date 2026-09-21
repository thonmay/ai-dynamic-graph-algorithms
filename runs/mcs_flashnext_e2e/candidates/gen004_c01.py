"""Dynamic MCS (undirected): maintain a maximum-cardinality-search ordering.

Derived from the bucket-suffix parent (keep the order pi, rerun only the
suffix an edge flip can invalidate), with these mutations:

1. State addition: cnt_sel[w], the cardinality w had at its own selection
   step, plus buckets: a list of vertex sets keyed by cnt_sel value, and a
   running maxcnt upper bound. No segment tree.
2. Insert fast path (no rerun). Insert (u,v), pos[u] < pos[v], raises only
   v's count, by exactly 1, at steps in (pos[u], pos[v]); steps <= pos[u]
   are untouched, from pos[v] on v is chosen with a raised count so its own
   step stays valid, and every other vertex keeps identical counts at every
   step. The order survives iff v's old count never ties the old step max
   in the window (old validity gives <=, so a tie means the raised count
   strictly exceeds it). A carried count with O(1) set lookups finds the
   first tie in O(window + deg(v)).
3. Delete fast path, exact. Delete (u,v), pos[u] < pos[v], lowers only v's
   count; every earlier step keeps its chosen vertex as the old max
   witness, and later steps are unchanged, so only step p = pos[v] can
   break. It breaks iff some later vertex w has exact prefix-count at step
   p of at least cnt_sel[v]; since that count is at most cnt_sel[w], only
   vertices in buckets >= cnt_sel[v] can break it, so scanning those
   buckets with exact counts is a complete test, not a sufficient one.
   Cases where the order stays valid despite a later vertex having a high
   selection count skip the rerun entirely.
4. Rerun with early stop. The bucket MCS rerun stops once the picked set
   equals the old positions p..k and v has been picked: u is always in the
   untouched prefix, so every unchosen vertex keeps identical neighborhoods
   and prefix sets, and the old tail is still a valid MCS suffix. cnt_sel
   and the buckets are point-updated for every vertex the rerun picks.

Tie-breaking is by bucket pop order (LIFO); the invariant only requires
each pick to have maximum cardinality, not a specific tie-break.
"""


def _rerun(order, pos, p, adj, n, cnt_sel, buckets, v):
    """Bucket MCS over order[p:] with order[:p] chosen, with early stop.

    `pos` holds the OLD positions during the rerun. Stops once the picked
    set equals old positions p..k and v has been picked; the old tail
    order[k+1:] is then still a valid MCS suffix and is appended as is.
    Refreshes cnt_sel and the cnt_sel buckets for every vertex it picks.
    Returns (suffix, stop, run_max) with run_max the largest selection
    count recorded during the run.
    """
    chosen = [False] * n
    for i in range(p):
        chosen[order[i]] = True
    cnt = [0] * n
    lb = [[] for _ in range(n + 1)]  # lazy radix buckets for the run
    top = 0
    for i in range(p, n):
        w = order[i]
        c = 0
        for x in adj[w]:
            if chosen[x]:
                c += 1
        cnt[w] = c
        lb[c].append(w)
        if c > top:
            top = c
    picked = []
    max_pos_picked = p - 1
    v_picked = False
    remaining = n - p
    stop = n - 1
    run_max = 0
    while remaining:
        while not lb[top]:
            top -= 1
        w = lb[top].pop()
        if chosen[w] or cnt[w] != top:
            continue  # stale lazy-bucket entry
        chosen[w] = True
        remaining -= 1
        picked.append(w)
        if top > run_max:
            run_max = top
        if cnt_sel[w] != top:
            buckets[cnt_sel[w]].remove(w)
            cnt_sel[w] = top
            buckets[top].add(w)
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
                lb[cnt[x]].append(x)
                if cnt[x] > top:
                    top = cnt[x]
    return picked, stop, run_max


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
    buckets = [set() for _ in range(n + 1)]
    for w in range(n):
        buckets[0].add(w)
    # v = -1 is never picked, so the initial run never stops early.
    order, _, run_max = _rerun(list(range(n)), [0] * n, 0, adj, n,
                               cnt_sel, buckets, -1)
    pos = [0] * n
    for i, w in enumerate(order):
        pos[w] = i
    return {"n": n, "adj": adj, "order": order, "pos": pos,
            "cnt_sel": cnt_sel, "buckets": buckets, "maxcnt": run_max}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].add(v)
    adj[v].add(u)
    pos = state["pos"]
    order = state["order"]
    cnt_sel = state["cnt_sel"]
    buckets = state["buckets"]
    n = state["n"]
    if pos[u] > pos[v]:
        u, v = v, u
    pu, pv = pos[u], pos[v]
    # v's OLD count at step pu+1: new neighbors of v chosen by then, minus
    # u (u is chosen at step pu, not before it, and was not an old neighbor).
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
        old = cnt_sel[v]
        buckets[old].remove(v)
        cnt_sel[v] = old + 1
        buckets[old + 1].add(v)
        if old + 1 > state["maxcnt"]:
            state["maxcnt"] = old + 1
        return state
    suffix, stop, run_max = _rerun(order, pos, i0, adj, n, cnt_sel,
                                   buckets, v)
    order[i0:] = suffix
    for i in range(i0, stop + 1):
        pos[order[i]] = i
    if run_max > state["maxcnt"]:
        state["maxcnt"] = run_max
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state["adj"]
    adj[u].discard(v)
    adj[v].discard(u)
    pos = state["pos"]
    order = state["order"]
    cnt_sel = state["cnt_sel"]
    buckets = state["buckets"]
    n = state["n"]
    if pos[u] > pos[v]:
        u, v = v, u
    p = pos[v]
    cv = cnt_sel[v]
    # Only step p can break: v's count drops to cv - 1 there and every
    # other unchosen vertex keeps its count, which at step p is at most its
    # own selection count. A later vertex can beat v's new count only from
    # a bucket >= cv, so an exact scan of those buckets decides.
    breaks = False
    for c in range(state["maxcnt"], cv - 1, -1):
        for w in buckets[c]:
            if pos[w] > p:
                cp = 0
                for x in adj[w]:
                    if pos[x] < p:
                        cp += 1
                if cp >= cv:
                    breaks = True
                    break
        if breaks:
            break
    if not breaks:
        buckets[cv].remove(v)
        cnt_sel[v] = cv - 1
        buckets[cv - 1].add(v)
        maxc = state["maxcnt"]
        while maxc > 0 and not buckets[maxc]:
            maxc -= 1
        state["maxcnt"] = maxc
        return state
    suffix, stop, run_max = _rerun(order, pos, p, adj, n, cnt_sel,
                                   buckets, v)
    order[p:] = suffix
    for i in range(p, stop + 1):
        pos[order[i]] = i
    if run_max > state["maxcnt"]:
        state["maxcnt"] = run_max
    return state
