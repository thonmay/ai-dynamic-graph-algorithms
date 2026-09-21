"""Dynamic Maximum Cardinality Search (MCS) ordering, undirected graphs.

Maintains a vertex ordering that is a valid MCS ordering of the current
graph: each vertex is chosen when its cardinality (number of already-chosen
neighbors) is maximal among the unchosen vertices (ties broken by smallest id).

Mutation of the window-scan parent: the repair probes no longer recompute
selection cardinalities with popcounts. Three structures are maintained:
  - card_at[k]: cardinality of order[k] at its selection step. Flipping edge
    (u, v) with pos[u] < pos[v] changes exactly one entry, card_at[pos[v]]
    (+1 on insertion, -1 on deletion), because the flip is incident only to
    u and v and u is already chosen at every step from pos[u] on.
  - buckets[c]: bitmask of steps whose card_at equals c, plus peak = highest
    nonempty bucket. On deletion the only breaking step is pos[v], and an
    unchosen w can beat v there only if its selection cardinality is at least
    v's new one (cw <= card_at[i] since prefix_pv is a subset of prefix_i),
    so the probe iterates only the bucket candidates above pv instead of
    scanning the whole suffix.
  - pref[k]: bitmask of order[:k], so probe seeds are O(1) lookups.
The affected-window argument is the parent's: insertion can only break steps
pos[u]+1..pos[v] (step pos[v] itself never breaks: v's cardinality strictly
rose), deletion can only break step pos[v]. The insertion probe reads c
straight from card_at[k] and tracks v's cardinality incrementally. Bucket MCS
regreedy (Rose-Tarjan, smallest id first) runs from the first breaking step
and refreshes card_at, buckets, pref and peak for the rewritten suffix.
"""


def _regreedy(st, k0):
    """Re-run bucket MCS on order[k0:], keeping order[:k0] fixed, and
    refresh card_at, buckets, pref and peak for the rewritten suffix."""
    n = st["n"]
    mask = st["mask"]
    order = st["order"]
    pos = st["pos"]
    card_at = st["card_at"]
    buckets = st["buckets"]
    pref = st["pref"]
    # drop the old suffix from the step buckets
    for i in range(k0, n):
        buckets[card_at[i]] &= ~(1 << i)
    remaining = 0
    for i in range(k0, n):
        remaining |= 1 << order[i]
    if not remaining:
        return
    prefix = pref[k0]
    card = [0] * n
    vb = [0] * (n + 1)  # vertex-id buckets during selection
    maxc = 0
    r = remaining
    while r:
        b = r & -r
        r ^= b
        v = b.bit_length() - 1
        c = (mask[v] & prefix).bit_count()
        card[v] = c
        vb[c] |= b
        if c > maxc:
            maxc = c
    k = k0
    suffix_peak = 0
    while remaining:
        while not vb[maxc]:
            maxc -= 1
        b = vb[maxc] & -vb[maxc]  # smallest id in top bucket
        vb[maxc] ^= b
        v = b.bit_length() - 1
        remaining ^= b
        order[k] = v
        pos[v] = k
        card_at[k] = maxc
        buckets[maxc] |= 1 << k
        pref[k + 1] = pref[k] | b
        if maxc > suffix_peak:
            suffix_peak = maxc
        k += 1
        nb = mask[v] & remaining
        while nb:
            b = nb & -nb
            nb ^= b
            w = b.bit_length() - 1
            vb[card[w]] ^= b
            card[w] += 1
            vb[card[w]] |= b
            if card[w] > maxc:
                maxc = card[w]
    if suffix_peak > st["peak"]:
        st["peak"] = suffix_peak
    while st["peak"] > 0 and not buckets[st["peak"]]:
        st["peak"] -= 1


def _first_break(st, pu, pv, v):
    """Insertion repair probe. v's selection-time cardinality rose by one for
    every prefix from step pu+1 on; all other unchosen cardinalities are
    unchanged, and order[k] is neither u nor v for k in [pu+1, pv), so the old
    choice's cardinality is exactly card_at[k]. Step k breaks iff the new max
    is v: d > c, or d == c and v < order[k]. Step pv never breaks (v's own
    cardinality strictly rose). Return the first breaking step, or None."""
    order = st["order"]
    card_at = st["card_at"]
    mask = st["mask"]
    d = (mask[v] & st["pref"][pu + 1]).bit_count()
    for k in range(pu + 1, pv):
        c = card_at[k]
        if d > c or (d == c and v < order[k]):
            return k
        if (mask[v] >> order[k]) & 1:
            d += 1
    return None


def _deletion_breaks(st, pv, v):
    """Deletion repair probe. Only step pv can break: v's cardinality there
    dropped to c = card_at[pv] - 1, every other unchosen cardinality cw is
    unchanged and at most c + 1. The step breaks iff some unchosen w has
    cw > c, or cw == c and w < v. A w with card_at < c can never reach c, so
    only the bucket candidates above pv are visited."""
    order = st["order"]
    card_at = st["card_at"]
    buckets = st["buckets"]
    mask = st["mask"]
    c = card_at[pv] - 1
    cand = 0
    for cc in range(c, st["peak"] + 1):
        cand |= buckets[cc]
    cand &= ~((1 << (pv + 1)) - 1)  # steps strictly after pv
    prefix = st["pref"][pv]
    while cand:
        b = cand & -cand
        cand ^= b
        w = order[b.bit_length() - 1]
        cw = (mask[w] & prefix).bit_count()
        if cw > c or (cw == c and w < v):
            return True
    return False


def init(graph):
    n = len(graph)
    mask = [0] * n
    for u in range(n):
        row = graph[u]
        m = 0
        for v in range(n):
            if row[v]:
                m |= 1 << v
        mask[u] = m
    st = {
        "n": n,
        "mask": mask,
        "order": list(range(n)),
        "pos": [0] * n,
        "card_at": [0] * n,
        "buckets": [0] * (n + 1),
        "pref": [0] * (n + 1),
        "peak": 0,
    }
    _regreedy(st, 0)
    return st


def _update(edge, state, present):
    u, v = edge
    mask = state["mask"]
    if present:
        mask[u] |= 1 << v
        mask[v] |= 1 << u
    else:
        mask[u] &= ~(1 << v)
        mask[v] &= ~(1 << u)
    pos = state["pos"]
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu
    # v is the later endpoint: the only vertex whose selection-time
    # cardinality the flip changes, and card_at[pv] its sole card_at entry.
    if present:
        k = _first_break(state, pu, pv, v)
    else:
        k = pv if _deletion_breaks(state, pv, v) else None
    if k is not None:
        _regreedy(state, k)
    else:
        card_at = state["card_at"]
        buckets = state["buckets"]
        buckets[card_at[pv]] &= ~(1 << pv)
        card_at[pv] += 1 if present else -1
        buckets[card_at[pv]] |= 1 << pv
        if present:
            if card_at[pv] > state["peak"]:
                state["peak"] = card_at[pv]
        else:
            while state["peak"] > 0 and not buckets[state["peak"]]:
                state["peak"] -= 1
    return state


def insert_edge(graph, edge, state):
    return _update(edge, state, True)


def delete_edge(graph, edge, state):
    return _update(edge, state, False)
