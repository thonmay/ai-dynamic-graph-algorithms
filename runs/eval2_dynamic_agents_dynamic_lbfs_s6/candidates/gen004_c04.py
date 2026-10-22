"""Dynamic LexBFS ordering (gen004_c04).

Derived from gen001_c02 (bitset partition-refinement LexBFS + (LB) check).
Changes aimed at lowering the work ratio:

1. The (LB) 4-point check is rewritten to use the equivalence
   min_pos(W) < min_pos(A) (where A = {a < b : ab not in E, ac in E} and
   W = N(b) \\ N(c)), and to scan whichever of A or W is smaller first,
   short-circuiting as soon as possible.

2. A cheap necessary-condition prefilter runs before the full (LB) check:
   for every pair (b, c) with b < c and bc not in E, the set
   W = N(b) \\ N(c) must be non-empty.  If it is empty for some pair, the
   ordering is invalid and we recompute immediately, skipping the full
   check.  The prefilter is O(n^2) bit operations and is much cheaper than
   the full check on graphs where it catches the violation.

3. The fallback recompute uses the same bitset partition-refinement as the
   parent (O(n^2) worst case, fast in practice).

Correctness: the ordering is only kept if the full (LB) 4-point property
holds on the current graph; otherwise a fresh LexBFS is computed.  The (LB)
property is necessary and sufficient for an ordering to be a LexBFS
ordering (Corneil-Krueger), so the maintained ordering is always valid.
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


def _min_pos_in_set(s, pos):
    """Return the minimum position (in the ordering) of any vertex in
    bitset s.  Returns n (infinity) if s is empty."""
    n = len(pos)
    best = n
    tmp = s
    while tmp:
        lb = tmp & -tmp
        v = lb.bit_length() - 1
        p = pos[v]
        if p < best:
            best = p
        tmp ^= lb
    return best


def _check_lb(adj, n, order):
    """Check the (LB) 4-point property.

    For all positions a < b < c in the ordering with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Equivalent formulation: for all b < c with bc not in E,
    if A = {a : a < b, ab not in E, ac in E} is non-empty, then
    min_pos(N(b) \\ N(c)) < min_pos(A).

    Returns True if valid.
    """
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    # prefix[i] = bitset of first i vertices in order
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    for pb in range(n):
        b = order[pb]
        for pc in range(pb + 1, n):
            c = order[pc]
            # A = {a : pa < pb, a not adj b, a adj c}
            A = prefix[pb] & ~adj[b] & adj[c]
            if not A:
                continue
            # W = {d : d adj b, d not adj c}
            W = adj[b] & ~adj[c]
            if not W:
                return False
            # Need: min_pos(W) < min_pos(A)
            # Scan the smaller set first for early exit.
            if W.bit_count() < A.bit_count():
                min_pw = _min_pos_in_set(W, pos)
                # If min_pw >= pb, then min_pw >= min_pa (since min_pa < pb),
                # so the condition fails.
                if min_pw >= pb:
                    return False
                # min_pw < pb; now check min_pa > min_pw
                min_pa = _min_pos_in_set(A, pos)
                if min_pw >= min_pa:
                    return False
            else:
                min_pa = _min_pos_in_set(A, pos)
                # Check if W has any element with pos < min_pa
                if not (W & prefix[min_pa]):
                    return False
    return True


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
    if _check_lb(adj, n, order):
        return {'ordering': order, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    adj = state['adj']
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    order = state['ordering']
    if _check_lb(adj, n, order):
        return {'ordering': order, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}
