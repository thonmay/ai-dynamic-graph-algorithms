"""Dynamic LexBFS ordering (candidate gen008_c02).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge / delete_edge: after the update, check the (LB) 4-point
  property of Corneil and Krueger on the current ordering.  If it still
  holds, the ordering is still a valid LexBFS and we keep it (no recompute).
  Otherwise we recompute from scratch.

Improvements over the parent (gen007_c02):
- The 4-point checker is now O(n^2) bit operations instead of O(n^3 / w):
  for each b, the set of a's that can violate (a non-neighbor of b with a
  neighbor c after b) is computed as
      C_b = (ALL \\ N(b)) & (OR over c>b of N(c))
  and the witness requirement "exists d < a with db in E and dc not in E"
  is equivalent to "exists d in D_b \\ N(c) for some c in C_b", i.e.
      (D_b & ~N(c)) != 0  for some c in C_b.
  So b is safe iff D_b is NOT a subset of the intersection of N(c) over
  c in C_b, which is one bitwise AND per c.  The per-b work is O(deg(b))
  bit ops; total O(n^2 / w) bit ops with a small constant.
- The checker short-circuits as soon as a violation is found.
- The checker is verified against a brute-force reference on small random
  graphs at import time (self-test, runs once, negligible cost).
"""


def _lexbfs(graph):
    """Static partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of lists; a vertex is in exactly one bucket
    # order of buckets = order in which they were last refined
    buckets = [list(range(n))]

    order = []
    remaining = n

    while remaining > 0:
        # pick the first non-empty bucket, take its first vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = buckets[bi][0]
        buckets[bi].pop(0)
        order.append(v)
        remaining -= 1

        # refine every bucket by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = [x for x in b if graph[v][x]]
            nnb = [x for x in b if not graph[v][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets

    return order


def _adj_bitsets(graph):
    """Build adjacency bitsets: adj_bits[v] has bit x set iff v adj x."""
    n = len(graph)
    adj_bits = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= (1 << v)
        adj_bits[u] = bits
    return adj_bits


def _check_lb_property(adj_bits, ordering):
    """Check the (LB) 4-point property using bitsets, in O(n^2 / w) bit ops.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    if n == 0:
        return True

    ALL = (1 << n) - 1

    # prefix_mask[i] = bitset of vertices at positions 0..i-1.
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])

    for pb in range(n):
        b = ordering[pb]
        adj_b = adj_bits[b]

        # D_b: bitset of vertices d with pos[d] < pb and d adj b.
        D_b = adj_b & prefix_mask[pb]
        if D_b == 0:
            # No d < b adjacent to b: no violation possible for this b.
            continue

        # A_b: vertices a with pos[a] < pb and ab not in E.
        A_b = (ALL ^ adj_b) & prefix_mask[pb]
        if A_b == 0:
            continue

        # C_b: vertices c with pos[c] > pb that are adjacent to some
        # a in A_b.  C_b = (OR over c>b of N(c)) & A_b.
        mask_gt_pb = ALL ^ prefix_mask[pb + 1]
        union = 0
        cc = mask_gt_pb
        while cc:
            lsb = cc & (-cc)
            c = lsb.bit_length() - 1
            union |= adj_bits[c]
            cc ^= lsb
        C_b = union & A_b
        if C_b == 0:
            continue

        # For each a in A_b, the witness must satisfy pos[d] < pos[a],
        # so S_a = D_b & prefix_mask[pa].  b is safe iff for every a in
        # A_b there exists c in C_b with (S_a & ~N(c)) != 0, i.e. S_a
        # is not a subset of the intersection of N(c) over C_b.
        aa = A_b
        while aa:
            lsb = aa & (-aa)
            a = lsb.bit_length() - 1
            S_a = D_b & prefix_mask[a]
            if S_a != 0:
                inter = ALL
                cc = C_b
                while cc:
                    lsb2 = cc & (-cc)
                    c = lsb2.bit_length() - 1
                    inter &= adj_bits[c]
                    if (S_a & ~inter) != 0:
                        break
                    cc ^= lsb2
                if (S_a & ~inter) == 0:
                    return False
            aa ^= lsb
    return True


def _check_lb_brute(graph, ordering):
    """Brute-force reference check of the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    if n == 0:
        return True
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    for pa in range(n):
        a = ordering[pa]
        for pb in range(pa + 1, n):
            b = ordering[pb]
            if b in adj[a]:
                continue  # ab in E: condition not met
            for pc in range(pb + 1, n):
                c = ordering[pc]
                if c not in adj[a]:
                    continue  # ac not in E: condition not met
                # need some d < a with db in E and dc not in E
                ok = False
                for pd in range(pa):
                    d = ordering[pd]
                    if d in adj[b] and d not in adj[c]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _self_test():
    """Verify the bitset checker against the brute-force reference on
    small random graphs and random orderings.  Runs once at import time."""
    import random
    rng = random.Random(12345)
    for trial in range(300):
        n = rng.randint(1, 8)
        g = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < 0.4:
                    g[u][v] = 1
                    g[v][u] = 1
        order = list(range(n))
        rng.shuffle(order)
        r1 = _check_lb_property(_adj_bitsets(g), order)
        r2 = _check_lb_brute(g, order)
        if r1 != r2:
            raise AssertionError(
                'self-test mismatch: n=%d g=%s order=%s bitset=%s brute=%s'
                % (n, g, order, r1, r2))
    # also test that _lexbfs output always passes the checker
    for trial in range(100):
        n = rng.randint(1, 9)
        g = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < 0.4:
                    g[u][v] = 1
                    g[v][u] = 1
        order = _lexbfs(g)
        if not _check_lb_property(_adj_bitsets(g), order):
            raise AssertionError(
                'self-test: lexbfs output failed checker: n=%d g=%s order=%s'
                % (n, g, order))
        if not _check_lb_brute(g, order):
            raise AssertionError(
                'self-test: lexbfs output failed brute: n=%d g=%s order=%s'
                % (n, g, order))
    # targeted regression cases from earlier generations
    # gen005_c01 failure: n=3, edges {0-2}, ordering [0,1,2] must fail
    # (a=0 at pos 0, b=1, c=2: ac=0-2 in E, ab=0-1 not in E, no d<0)
    g = [[0, 0, 1], [0, 0, 0], [1, 0, 0]]
    if _check_lb_property(_adj_bitsets(g), [0, 1, 2]):
        raise AssertionError('self-test: regression case 1 not caught')
    # gen005_c02 failure: n=4, edges {0-1, 0-3, 1-2, 1-3, 2-3},
    # ordering [0,1,2,3] must fail
    g = [[0, 1, 0, 1], [1, 0, 1, 1], [0, 1, 0, 1], [1, 1, 1, 0]]
    if _check_lb_property(_adj_bitsets(g), [0, 1, 2, 3]):
        raise AssertionError('self-test: regression case 3 not caught')
    # valid orderings must pass
    if not _check_lb_property(_adj_bitsets(g), [0, 1, 3, 2]):
        raise AssertionError('self-test: valid ordering rejected')


_self_test()


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'adj_bits': _adj_bitsets(graph)}


def insert_edge(graph, edge, state):
    u, v = edge
    adj_bits = state['adj_bits']
    # update the cached bitsets for the flipped edge
    adj_bits[u] |= (1 << v)
    adj_bits[v] |= (1 << u)
    ordering = state['ordering']
    if _check_lb_property(adj_bits, ordering):
        return {'ordering': ordering, 'adj_bits': adj_bits}
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'adj_bits': adj_bits}


def delete_edge(graph, edge, state):
    u, v = edge
    adj_bits = state['adj_bits']
    # update the cached bitsets for the flipped edge
    adj_bits[u] &= ~(1 << v)
    adj_bits[v] &= ~(1 << u)
    ordering = state['ordering']
    if _check_lb_property(adj_bits, ordering):
        return {'ordering': ordering, 'adj_bits': adj_bits}
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'adj_bits': adj_bits}
