"""Dynamic LexBFS ordering (gen005_c04).

Derived from parent gen005_c03 (which derived from gen001_c02).  The
parent's plateau: on every update it either runs the O(n^2) (LB) check
(deletions) or the O(n) insertion check, and whenever the check fails it
pays a full O(n^2) partition-refinement recompute.  The work ratio is
dominated by the recompute cost on the updates where the old ordering is
no longer valid.

Changes in this candidate:

1.  Local repair before recompute.  When the (LB) check fails, instead of
    immediately recomputing, try a small set of cheap candidate orderings
    (swap u/v, move u or v next to the other, move u or v to the front or
    back) and accept the first one that passes the (LB) check.  Each
    candidate is verified with the full (LB) property, so correctness is
    preserved: we only ever return an ordering that is certified valid.
    On many updates the old ordering is "almost" valid and one of these
    local moves fixes it, avoiding the O(n^2) recompute.

2.  The (LB) check itself is unchanged from the parent (O(n^2) bitset
    check for deletions, O(n) targeted check for insertions).

3.  The fallback recompute is the same bitset partition-refinement LexBFS
    as the parent.

Correctness argument: the returned ordering is either (a) the previous
ordering, which passed the (LB) 4-point property check on the current
graph, or (b) a candidate produced by a local move, which also passed the
(LB) check, or (c) a fresh partition-refinement LexBFS, which is a valid
LexBFS ordering by construction.  The (LB) property is necessary and
sufficient for an ordering to be a LexBFS ordering (Corneil-Krueger), so
every returned ordering is valid.
"""


def _bitsets(graph):
    n = len(graph)
    adj = [0] * n
    for i in range(n):
        row = graph[i]
        b = 0
        for j in range(n):
            if row[j]:
                b |= 1 << j
        adj[i] = b
    return adj


def _lexbfs(adj, n):
    """Partition-refinement LexBFS using bitsets. Returns ordering list."""
    if n == 0:
        return []
    order = []
    remaining = (1 << n) - 1
    buckets = [remaining]

    for _ in range(n):
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        B = buckets[bi]
        v = (B & -B).bit_length() - 1
        Bv = 1 << v
        B &= ~Bv
        remaining &= ~Bv
        order.append(v)

        Nv = adj[v]
        new_buckets = []
        for i, C in enumerate(buckets):
            if i == bi:
                C = B
            Cn = C & Nv
            Cnot = C & ~Nv
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets

    return order


def _min_pos_in_set(A, pos):
    """Find the minimum position among vertices in bitset A."""
    min_pa = 1 << 62
    tmp = A
    while tmp:
        lb = tmp & -tmp
        a = lb.bit_length() - 1
        pa = pos[a]
        if pa < min_pa:
            min_pa = pa
        tmp ^= lb
    return min_pa


def _check_lb_full(adj, n, order):
    """Full (LB) 4-point property check. O(n^2) bit ops."""
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    for pb in range(n):
        b = order[pb]
        adjb = adj[b]
        for pc in range(pb + 1, n):
            c = order[pc]
            A = prefix[pb] & ~adjb & adj[c]
            if not A:
                continue
            W = adjb & ~adj[c]
            if not W:
                return False
            min_pa = _min_pos_in_set(A, pos)
            if not (W & prefix[min_pa]):
                return False
    return True


def _check_lb_insert(adj, n, order, u, v):
    """Check (LB) after inserting edge (u,v).

    Adding edge (u,v) can only create new violations where the new edge
    serves as the 'ac' edge in the (LB) property:
      for positions a < b < c with ac in E (new) and ab not in E,
      need d < a with db in E and dc not in E.

    So we only check triples where {a,c} = {u,v}:
      Case 1: a=u, c=v (pos[u] < pos[v])
      Case 2: a=v, c=u (pos[v] < pos[u])
    For each, b ranges over positions between a and c.
    This is O(n) instead of O(n^2).
    """
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    pu = pos[u]
    pv = pos[v]

    if pu < pv:
        for pb in range(pu + 1, pv):
            b = order[pb]
            if adj[u] & (1 << b):
                continue
            W = adj[b] & ~adj[v]
            if not (W & prefix[pu]):
                return False

    if pv < pu:
        for pb in range(pv + 1, pu):
            b = order[pb]
            if adj[v] & (1 << b):
                continue
            W = adj[b] & ~adj[u]
            if not (W & prefix[pv]):
                return False

    return True


def _local_repair(adj, n, order, u, v):
    """Try a small set of local moves to fix the ordering.

    Returns a new ordering if one of the candidates passes the full (LB)
    check, else None.  The candidates are cheap to construct (O(n) each)
    and each is verified with the full (LB) check, so correctness is
    guaranteed.
    """
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    pu, pv = pos[u], pos[v]
    if pu == pv:
        return None

    candidates = []

    # 1. Swap u and v.
    o = list(order)
    o[pu], o[pv] = o[pv], o[pu]
    candidates.append(o)

    # 2. Move v to just before u.
    o = list(order)
    o.pop(pv)
    pu2 = pu - 1 if pv < pu else pu
    o.insert(pu2, v)
    candidates.append(o)

    # 3. Move u to just before v.
    o = list(order)
    o.pop(pu)
    pv2 = pv - 1 if pu < pv else pv
    o.insert(pv2, u)
    candidates.append(o)

    # 4. Move v to just after u.
    o = list(order)
    o.pop(pv)
    pu2 = pu - 1 if pv < pu else pu
    o.insert(pu2 + 1, v)
    candidates.append(o)

    # 5. Move u to just after v.
    o = list(order)
    o.pop(pu)
    pv2 = pv - 1 if pu < pv else pv
    o.insert(pv2 + 1, u)
    candidates.append(o)

    # 6. Move v to the front.
    if pv != 0:
        o = list(order)
        o.pop(pv)
        o.insert(0, v)
        candidates.append(o)

    # 7. Move u to the front.
    if pu != 0:
        o = list(order)
        o.pop(pu)
        o.insert(0, u)
        candidates.append(o)

    # 8. Move v to the back.
    if pv != n - 1:
        o = list(order)
        o.pop(pv)
        o.append(v)
        candidates.append(o)

    # 9. Move u to the back.
    if pu != n - 1:
        o = list(order)
        o.pop(pu)
        o.append(u)
        candidates.append(o)

    for cand in candidates:
        if _check_lb_full(adj, n, cand):
            return cand
    return None


def init(graph):
    n = len(graph)
    adj = _bitsets(graph)
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    adj = state['adj']
    adj[u] |= 1 << v
    adj[v] |= 1 << u
    order = state['ordering']
    if _check_lb_insert(adj, n, order, u, v):
        return {'ordering': order, 'adj': adj, 'n': n}
    fixed = _local_repair(adj, n, order, u, v)
    if fixed is not None:
        return {'ordering': fixed, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    adj = state['adj']
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    order = state['ordering']
    if _check_lb_full(adj, n, order):
        return {'ordering': order, 'adj': adj, 'n': n}
    fixed = _local_repair(adj, n, order, u, v)
    if fixed is not None:
        return {'ordering': fixed, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}
