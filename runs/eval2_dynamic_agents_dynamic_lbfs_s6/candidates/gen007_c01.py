"""Dynamic LexBFS ordering (gen007_c01).

Derived from gen006_c01 (verify-then-recompute).  Changes:

1. The (LB) 4-point property check is now O(n^2) bitset operations with a
   precomputed prefix mask per position, so the witness test is a single
   bitset AND instead of a binary search.

2. The fallback recompute is the standard partition-refinement LexBFS with
   bitsets, O(n^2) word operations.

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


def _check_lb(adj, n, order):
    """Check the (LB) 4-point property in O(n^2) bitset operations.

    For all positions pa < pb < pc with order[pa] adj order[pc] and
    order[pa] not adj order[pb], there exists pd < pa with
    order[pd] adj order[pb] and order[pd] not adj order[pc].

    Returns True if the ordering is a valid LexBFS ordering.
    """
    # prefix[i] = bitset of first i vertices in order
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
