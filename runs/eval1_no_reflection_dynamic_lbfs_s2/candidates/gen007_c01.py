"""Dynamic LexBFS ordering (gen007_c01).

Strategy: check-then-recompute, with an EXACT incremental (LB) 4-point
check after a single edge flip.

After flipping edge (u, v), a triple (a, b, c) with a < b < c can change
status only if the flipped edge is incident to at least one of {a, b, c}
(incident to zero: nothing changes; the constraint ac in E / ab not in E
and the witness condition db in E / dc not in E for d < a all involve only
edges among {a, b, c} and earlier vertices, so an edge touching none of
{a, b, c} cannot affect the triple).  The affected triples are exactly:

  C1: flipped edge = (a, b)          -> constraint ab flips
  C2: flipped edge = (a, c)          -> constraint ac flips
  C3: flipped edge = (d, b), d < a   -> witness db flips
  C4: flipped edge = (d, c), d < a   -> witness dc flips

All four are re-verified with bitsets over positions, O(n^2) per update.
If any affected triple is violated, recompute a fresh LexBFS (HMPV
partition refinement) from the current matrix.  Correctness: the ordering
was valid before the flip; only affected triples can become violated; we
check all of them exactly.
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


def _witness_ok(order, masks, prefix, a, b, c):
    """Witness test for triple (a, b, c): exists d < a with db in E and
    dc not in E.  Positions a < b < c assumed."""
    va, vb, vc = order[a], order[b], order[c]
    return (prefix[a] & masks[vb] & ~masks[vc]) != 0


def _check_after_flip(order, masks, u, v):
    """Exact incremental (LB) check after flipping edge (u, v).

    Re-verifies every triple whose status can have changed (cases C1-C4
    in the module docstring).  Returns True iff the ordering is still a
    valid LexBFS.
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    pu, pv = pos[u], pos[v]

    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    # C1: flipped edge = (a, b).  The pair (a, b) is exactly (pu, pv).
    # If ab is now not in E: for every c > b with ac in E, need a witness.
    a, b = (pu, pv) if pu < pv else (pv, pu)
    va, vb = order[a], order[b]
    ma, mb = masks[va], masks[vb]
    if not (ma & (1 << vb)):
        for c in range(b + 1, n):
            vc = order[c]
            if (ma & (1 << vc)) and not _witness_ok(order, masks, prefix, a, b, c):
                return False

    # C2: flipped edge = (a, c).  a is one endpoint, c the other, a < c.
    # If ac is now in E: for every b in (a, c) with ab not in E, need a
    # witness.  (If ac is now not in E, the constraint is gone: safe.)
    for a in (pu, pv):
        va = order[a]
        c = pv if a == pu else pu
        if a >= c:
            continue
        vc = order[c]
        ma = masks[va]
        if not (ma & (1 << vc)):
            continue  # ac not in E: no constraint
        for b in range(a + 1, c):
            vb = order[b]
            if ma & (1 << vb):
                continue  # ab in E: no constraint
            if not _witness_ok(order, masks, prefix, a, b, c):
                return False

    # C3: flipped edge = (d, b) with d < a < b < c.  b is one endpoint,
    # d the other.  For every a with d < a < b and every c > b with
    # ac in E and ab not in E, re-check the witness.
    for b in (pu, pv):
        vb = order[b]
        d = pv if b == pu else pu
        mb = masks[vb]
        for a in range(d + 1, b):
            va = order[a]
            ma = masks[va]
            if ma & (1 << vb):
                continue  # ab in E: no constraint
            for c in range(b + 1, n):
                vc = order[c]
                if not (ma & (1 << vc)):
                    continue  # ac not in E: no constraint
                if not _witness_ok(order, masks, prefix, a, b, c):
                    return False

    # C4: flipped edge = (d, c) with d < a < b < c.  c is one endpoint,
    # d the other.  For every a with d < a < c and every b in (a, c)
    # with ac in E and ab not in E, re-check the witness.
    for c in (pu, pv):
        vc = order[c]
        d = pv if c == pu else pu
        mc = masks[vc]
        for a in range(d + 1, c):
            va = order[a]
            ma = masks[va]
            if not (ma & (1 << vc)):
                continue  # ac not in E: no constraint
            for b in range(a + 1, c):
                vb = order[b]
                if ma & (1 << vb):
                    continue  # ab in E: no constraint
                if not _witness_ok(order, masks, prefix, a, b, c):
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
