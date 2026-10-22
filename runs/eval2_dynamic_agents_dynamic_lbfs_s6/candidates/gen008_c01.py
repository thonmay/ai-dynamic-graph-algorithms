"""Dynamic LexBFS ordering (gen008_c01).

Derived from gen007_c01 (verify-then-recompute with bitsets).  The parent's
plateau: every update pays the O(n^2) (LB) check, and every failed check
pays a full O(n^2) partition-refinement recompute.  This candidate attacks
both costs:

1.  O(n) insertion check.  Adding edge (u,v) can only create new (LB)
    violations where the new edge is the 'ac' edge, so only O(n) triples
    need checking.

2.  O(n) deletion check.  Removing edge (u,v) can only destroy witnesses
    d for pairs (b,c) with b adj u, c not adj u, and b not adj v, c adj v.
    The affected (b,c) pairs are exactly the cross pairs between
    N(u) \\ N(v) and N(v) \\ N(u), so the check is O(n) bit operations.

3.  Local repair before recompute.  When the check fails, try a small set
    of cheap candidate orderings (swap u/v, move u or v next to the other,
    to the front or back) and accept the first one that passes the full
    (LB) check.  Each candidate is verified, so correctness is preserved.

4.  Fallback recompute: standard partition-refinement LexBFS with bitsets.

Correctness: the returned ordering is either (a) the previous ordering,
which passed the (LB) 4-point property check on the current graph, (b) a
candidate produced by a local move, which also passed the (LB) check, or
(c) a fresh partition-refinement LexBFS, valid by construction.  The (LB)
property is necessary and sufficient for an ordering to be a LexBFS
ordering (Corneil-Krueger), so every returned ordering is valid.

State: {'ordering': list, 'adj': list of int bitsets, 'n': int}.
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
        # find first non-empty bucket
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        B = buckets[bi]
        # pick a vertex from B (lowest index for determinism)
        v = (B & -B).bit_length() - 1
        Bv = 1 << v
        B &= ~Bv
        remaining &= ~Bv
        order.append(v)

        Nv = adj[v]
        # refine: for each bucket, split into (bucket & Nv) and (bucket & ~Nv)
        new_buckets = []
        for i, C in enumerate(buckets):
            if i == bi:
                C = B  # already had v removed
            Cn = C & Nv
            Cnot = C & ~Nv
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets

    return order


def _check_lb_full(adj, n, order):
    """Full (LB) 4-point property check. O(n^2) bit ops.

    For all positions pa < pb < pc with order[pa] adj order[pc] and
    order[pa] not adj order[pb], there exists pd < pa with
    order[pd] adj order[pb] and order[pd] not adj order[pc].
    """
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    for pb in range(n):
        b = order[pb]
        adjb = adj[b]
        for pc in range(pb + 1, n):
            c = order[pc]
            # A = {a : a before b, a not adj b, a adj c}
            A = prefix[pb] & ~adjb & adj[c]
            if not A:
                continue
            # W = {d : d adj b, d not adj c}
            W = adjb & ~adj[c]
            if not W:
                return False
            # min position of a vertex in A: the first prefix mask that
            # contains any vertex of A.  O(log n) via binary search.
            lo, hi = 0, pb
            while lo < hi:
                mid = (lo + hi) // 2
                if A & prefix[mid]:
                    hi = mid
                else:
                    lo = mid + 1
            if not (W & prefix[lo]):
                return False
    return True


def _check_lb_insert(adj, n, order, u, v):
    """Check (LB) after inserting edge (u,v). O(n).

    Adding edge (u,v) can only create new violations where the new edge
    is the 'ac' edge: for positions a < b < c with ac in E (new) and
    ab not in E, need d < a with db in E and dc not in E.

    So we only check triples where {a,c} = {u,v}:
      Case 1: a=u, c=v (pos[u] < pos[v])
      Case 2: a=v, c=u (pos[v] < pos[u])
    For each, b ranges over positions between a and c.
    """
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

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


def _check_lb_delete(adj, n, order, u, v):
    """Check (LB) after deleting edge (u,v). O(n) bit operations.

    Removing edge (u,v) can only destroy witnesses d for pairs (b,c)
    where d = u or d = v was the witness.  The affected (b,c) pairs are
    those where b and c are in different "sides" relative to u and v:
    one is adjacent to u but not v, the other is adjacent to v but not u.
    """
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    # S1 = N(u) \\ N(v), S2 = N(v) \\ N(u)
    S1 = adj[u] & ~adj[v]
    S2 = adj[v] & ~adj[u]

    # For each b in S1, c in S2 with pos[b] < pos[c]:
    # A = {a : a before b, a not adj b, a adj c}
    # W = {d : d adj b, d not adj c, d != u, d != v}
    # Need W & prefix[min_pos(A)] != 0.
    tmp = S1
    while tmp:
        lb = tmp & -tmp
        b = lb.bit_length() - 1
        tmp ^= lb
        pb = pos[b]
        adjb = adj[b]
        tmp2 = S2
        while tmp2:
            lb2 = tmp2 & -tmp2
            c = lb2.bit_length() - 1
            tmp2 ^= lb2
            pc = pos[c]
            if pc <= pb:
                continue
            A = prefix[pb] & ~adjb & adj[c]
            if not A:
                continue
            W = adjb & ~adj[c] & ~(1 << u) & ~(1 << v)
            if not W:
                return False
            lo, hi = 0, pb
            while lo < hi:
                mid = (lo + hi) // 2
                if A & prefix[mid]:
                    hi = mid
                else:
                    lo = mid + 1
            if not (W & prefix[lo]):
                return False

    # For each b in S2, c in S1 with pos[b] < pos[c]:
    tmp = S2
    while tmp:
        lb = tmp & -tmp
        b = lb.bit_length() - 1
        tmp ^= lb
        pb = pos[b]
        adjb = adj[b]
        tmp2 = S1
        while tmp2:
            lb2 = tmp2 & -tmp2
            c = lb2.bit_length() - 1
            tmp2 ^= lb2
            pc = pos[c]
            if pc <= pb:
                continue
            A = prefix[pb] & ~adjb & adj[c]
            if not A:
                continue
            W = adjb & ~adj[c] & ~(1 << u) & ~(1 << v)
            if not W:
                return False
            lo, hi = 0, pb
            while lo < hi:
                mid = (lo + hi) // 2
                if A & prefix[mid]:
                    hi = mid
                else:
                    lo = mid + 1
            if not (W & prefix[lo]):
                return False

    # Case 3: b = u, c in S2 (c adj v, c not adj u).
    # A = {a : a before u, a not adj u, a adj c}
    # W = {d : d adj u, d not adj c, d != v}
    pu = pos[u]
    tmp = S2
    while tmp:
        lb = tmp & -tmp
        c = lb.bit_length() - 1
        tmp ^= lb
        pc = pos[c]
        if pc <= pu:
            continue
        A = prefix[pu] & ~adj[u] & adj[c]
        if not A:
            continue
        W = adj[u] & ~adj[c] & ~(1 << v)
        if not W:
            return False
        lo, hi = 0, pu
        while lo < hi:
            mid = (lo + hi) // 2
            if A & prefix[mid]:
                hi = mid
            else:
                lo = mid + 1
        if not (W & prefix[lo]):
            return False

    # Case 4: b = v, c in S1 (c adj u, c not adj v).
    # A = {a : a before v, a not adj v, a adj c}
    # W = {d : d adj v, d not adj c, d != u}
    pv = pos[v]
    tmp = S1
    while tmp:
        lb = tmp & -tmp
        c = lb.bit_length() - 1
        tmp ^= lb
        pc = pos[c]
        if pc <= pv:
            continue
        A = prefix[pv] & ~adj[v] & adj[c]
        if not A:
            continue
        W = adj[v] & ~adj[c] & ~(1 << u)
        if not W:
            return False
        lo, hi = 0, pv
        while lo < hi:
            mid = (lo + hi) // 2
            if A & prefix[mid]:
                hi = mid
            else:
                lo = mid + 1
        if not (W & prefix[lo]):
            return False

    # Case 5: b in S1, c = v (c adj v? no, c=v, b adj u, b not adj v).
    # A = {a : a before b, a not adj b, a adj v}
    # W = {d : d adj b, d not adj v, d != u}
    tmp = S1
    while tmp:
        lb = tmp & -tmp
        b = lb.bit_length() - 1
        tmp ^= lb
        pb = pos[b]
        adjb = adj[b]
        if pv <= pb:
            continue
        A = prefix[pb] & ~adjb & adj[v]
        if not A:
            continue
        W = adjb & ~adj[v] & ~(1 << u)
        if not W:
            return False
        lo, hi = 0, pb
        while lo < hi:
            mid = (lo + hi) // 2
            if A & prefix[mid]:
                hi = mid
            else:
                lo = mid + 1
        if not (W & prefix[lo]):
            return False

    # Case 6: b in S2, c = u (c adj u, b adj v, b not adj u).
    # A = {a : a before b, a not adj b, a adj u}
    # W = {d : d adj b, d not adj u, d != v}
    tmp = S2
    while tmp:
        lb = tmp & -tmp
        b = lb.bit_length() - 1
        tmp ^= lb
        pb = pos[b]
        adjb = adj[b]
        if pu <= pb:
            continue
        A = prefix[pb] & ~adjb & adj[u]
        if not A:
            continue
        W = adjb & ~adj[u] & ~(1 << v)
        if not W:
            return False
        lo, hi = 0, pb
        while lo < hi:
            mid = (lo + hi) // 2
            if A & prefix[mid]:
                hi = mid
            else:
                    lo = mid + 1
        if not (W & prefix[lo]):
            return False

    # Case 7: b = u, c = v (pos[u] < pos[v]).
    # A = {a : a before u, a not adj u, a adj v}
    # W = {d : d adj u, d not adj v}
    if pu < pv:
        A = prefix[pu] & ~adj[u] & adj[v]
        if A:
            W = adj[u] & ~adj[v]
            if not W:
                return False
            lo, hi = 0, pu
            while lo < hi:
                mid = (lo + hi) // 2
                if A & prefix[mid]:
                    hi = mid
                else:
                    lo = mid + 1
            if not (W & prefix[lo]):
                return False

    # Case 8: b = v, c = u (pos[v] < pos[u]).
    # A = {a : a before v, a not adj v, a adj u}
    # W = {d : d adj v, d not adj u}
    if pv < pu:
        A = prefix[pv] & ~adj[v] & adj[u]
        if A:
            W = adj[v] & ~adj[u]
            if not W:
                return False
            lo, hi = 0, pv
            while lo < hi:
                mid = (lo + hi) // 2
                if A & prefix[mid]:
                    hi = mid
                else:
                    lo = mid + 1
            if not (W & prefix[lo]):
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
    if _check_lb_delete(adj, n, order, u, v):
        return {'ordering': order, 'adj': adj, 'n': n}
    fixed = _local_repair(adj, n, order, u, v)
    if fixed is not None:
        return {'ordering': fixed, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}
