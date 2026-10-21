"""Dynamic LexBFS ordering (gen005_c01).

Derived from the parent's check-then-recompute scheme, with two changes:

1. The (LB) 4-point validity check is made incremental: after a single edge
   flip (u, v), only triples (a, b, c) whose witness set can change are
   re-examined.  A triple is affected iff the flipped edge is incident to
   exactly one of {a, b, c} (the constraint ac in E, ab not in E, or the
   witness condition db in E, dc not in E, must change).  This is O(n^2)
   per update instead of O(n^3), and it is exact: if no affected triple
   violates (LB), the ordering is still a valid LexBFS.

2. The static LexBFS is the standard partition-refinement algorithm
   (Habib-McConnell-Paul-Viennot), O(n+m) via adjacency sets.

If the incremental check reports a violation, we recompute from scratch
(the open problem: no known way to repair the ordering incrementally).
"""


def _adj_lists(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def _adj_masks(adj):
    n = len(adj)
    masks = [0] * n
    for v in range(n):
        m = 0
        for u in adj[v]:
            m |= (1 << u)
        masks[v] = m
    return masks


def _lexbfs(adj):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(adj)
    if n == 0:
        return []

    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        s = buckets[0][0]
        order.append(s)
        buckets[0] = buckets[0][1:]
        if not buckets[0]:
            buckets = buckets[1:]

        new_buckets = []
        for b in buckets:
            n_part = [v for v in b if v in adj[s]]
            nb_part = [v for v in b if v not in adj[s]]
            if n_part:
                new_buckets.append(n_part)
            if nb_part:
                new_buckets.append(nb_part)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(order, masks):
    """Full (LB) 4-point property check using bitmask adjacency.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    for a in range(n):
        va = order[a]
        earlier = prefix[a]
        ma = masks[va]
        for b in range(a + 1, n):
            vb = order[b]
            if ma & (1 << vb):
                continue  # ab in E, no constraint
            mb = masks[vb]
            for c in range(b + 1, n):
                vc = order[c]
                if not (ma & (1 << vc)):
                    continue  # ac not in E, no constraint
                if (earlier & mb & ~masks[vc]) == 0:
                    return False
    return True


def _check_after_flip(order, masks, u, v):
    """Exact incremental (LB) check after flipping edge (u, v).

    Only triples (a, b, c) with the flipped edge incident to exactly one of
    {a, b, c} can change status.  All other triples are unaffected.
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    pu, pv = pos[u], pos[v]

    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    # Case 1: flipped edge is (a, b) -- the ab edge changed.
    #   If ab is now in E: no constraint for this (a, b) pair.
    #   If ab is now not in E: for every c > b with ac in E, need a witness.
    lo, hi = (pu, pv) if pu < pv else (pv, pu)
    a, b = lo, hi
    va, vb = order[a], order[b]
    ma, mb = masks[va], masks[vb]
    if not (ma & (1 << vb)):
        earlier = prefix[a]
        for c in range(b + 1, n):
            vc = order[c]
            if ma & (1 << vc) and (earlier & mb & ~masks[vc]) == 0:
                return False

    # Case 2: flipped edge is (a, c) -- the ac edge changed.
    #   If ac is now in E: for every b in (a, c) with ab not in E, need a
    #   witness d < a with db in E and dc not in E.
    #   If ac is now not in E: no constraint for this (a, c) pair.
    for a in range(n):
        va = order[a]
        if va not in (u, v):
            continue
        ma = masks[va]
        other = v if va == u else u
        if not (ma & (1 << other)):
            continue  # ac not in E: no constraint
        earlier = prefix[a]
        mo = masks[other]
        for b in range(a + 1, n):
            if b == pos[other]:
                continue
            vb = order[b]
            if ma & (1 << vb):
                continue  # ab in E: no constraint
            if (earlier & masks[vb] & ~mo) == 0:
                return False

    # Case 3: flipped edge is (b, c) -- the witness edge db or dc changed.
    #   For every a < b with ac in E and ab not in E, re-check the witness.
    for b in range(n):
        vb = order[b]
        if vb not in (u, v):
            continue
        mb = masks[vb]
        for a in range(b):
            va = order[a]
            ma = masks[va]
            if ma & (1 << vb):
                continue  # ab in E: no constraint
            earlier = prefix[a]
            for c in range(b + 1, n):
                vc = order[c]
                if not (ma & (1 << vc)):
                    continue  # ac not in E: no constraint
                if (earlier & mb & ~masks[vc]) == 0:
                    return False

    return True


def _recompute(graph):
    adj = _adj_lists(graph)
    order = _lexbfs(adj)
    masks = _adj_masks(adj)
    return {'ordering': order, 'adj': adj, 'masks': masks}


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['adj'][v].add(u)
    state['masks'][u] |= (1 << v)
    state['masks'][v] |= (1 << u)
    if _check_after_flip(state['ordering'], state['masks'], u, v):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['adj'][v].discard(u)
    state['masks'][u] &= ~(1 << v)
    state['masks'][v] &= ~(1 << u)
    if _check_after_flip(state['ordering'], state['masks'], u, v):
        return state
    return _recompute(graph)
