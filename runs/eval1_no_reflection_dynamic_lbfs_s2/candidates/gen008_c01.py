"""Dynamic LexBFS ordering (gen008_c01).

Derived from gen007_c01 (exact incremental (LB) 4-point check after a single
edge flip, O(n^2) per update, recompute on violation).  One change:

The static LexBFS is now the classic HMPV partition-refinement algorithm
with a doubly-linked list of vertices and O(1) bucket splits (the "refine"
operation of the original paper), instead of the parent's O(n^2)
rebuild-every-step version.  Recomputes therefore cost O(n+m) instead of
O(n^2).

The incremental (LB) check is unchanged from the parent: after flipping
edge (u, v), only triples (a, b, c) whose status can change are re-verified
(cases C1-C4 below), using bitmask adjacency for O(1) witness tests.  If
any affected triple is violated, we recompute a fresh LexBFS from the
current matrix.

Correctness: the ordering was valid before the flip; only affected triples
can become violated; we check all of them exactly.  A fresh HMPV LexBFS is
always a valid LexBFS ordering.
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
    """Static LexBFS via HMPV partition refinement with linked buckets.

    Vertices form a doubly-linked list.  Buckets are contiguous segments
    of that list, tracked by (head, tail) pairs in a list.  When a vertex
    s is picked from the front of the first bucket, every other bucket is
    refined: split into (N(s) part, non-N(s) part), with the N(s) part
    first.  The split is done in O(|bucket|) by walking the segment and
    splicing the two pieces back into the vertex list.  Total cost over
    the whole run: O(n + m).
    """
    n = len(adj)
    if n == 0:
        return []

    # Doubly-linked list of all n vertices, initially 0, 1, ..., n-1.
    prev = [-1] * n
    nxt = [-1] * n
    for i in range(n - 1):
        nxt[i] = i + 1

    # Bucket list: list of (head, tail) pairs, in order.
    buckets = [(0, n - 1)]
    order = []

    for _ in range(n):
        # Pick the first vertex of the first bucket.
        s = buckets[0][0]
        order.append(s)

        # Remove s from the front of the first bucket.
        new_head = nxt[s]
        if new_head != -1:
            prev[new_head] = -1
            buckets[0] = (new_head, buckets[0][1])
        else:
            buckets = buckets[1:]

        # Refine every remaining bucket by adjacency to s.
        new_buckets = []
        for head, tail in buckets:
            # Walk the segment from head to tail, splitting into
            # N(s) and non-N(s) parts.
            n_head = -1
            n_tail = -1
            nb_head = -1
            nb_tail = -1
            cur = head
            while cur != -1 and cur != tail:
                if cur in adj[s]:
                    if n_head == -1:
                        n_head = cur
                    n_tail = cur
                else:
                    if nb_head == -1:
                        nb_head = cur
                    nb_tail = cur
                cur = nxt[cur]
            # Process the tail vertex.
            if cur == tail:
                if cur in adj[s]:
                    if n_head == -1:
                        n_head = cur
                    n_tail = cur
                else:
                    if nb_head == -1:
                        nb_head = cur
                    nb_tail = cur

            # Splice the two parts back into the vertex list.
            # The original segment was head..tail.  We replace it with
            # n_head..n_tail followed by nb_head..nb_tail (or just one
            # of them if the other is empty).
            pred = prev[head]
            succ = nxt[tail]

            # Connect n_tail to nb_head if both exist.
            if n_tail != -1 and nb_head != -1:
                nxt[n_tail] = nb_head
                prev[nb_head] = n_tail

            # Connect the new segment to the rest of the list.
            new_seg_head = n_head if n_head != -1 else nb_head
            new_seg_tail = nb_tail if nb_tail != -1 else n_tail

            if new_seg_head != -1:
                if pred != -1:
                    nxt[pred] = new_seg_head
                    prev[new_seg_head] = pred
                if succ != -1:
                    nxt[new_seg_tail] = succ
                    prev[succ] = new_seg_tail

            # Add the new buckets to the list.
            if n_head != -1:
                new_buckets.append((n_head, n_tail))
            if nb_head != -1:
                new_buckets.append((nb_head, nb_tail))

        buckets = new_buckets

    return order


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
