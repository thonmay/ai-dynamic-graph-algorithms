"""Dynamic LexBFS ordering (candidate gen006_c02).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge / delete_edge: after the update, check the (LB) 4-point
  property of Corneil and Krueger on the current ordering.  If it still
  holds, the ordering is still a valid LexBFS and we keep it (no recompute).
  Otherwise we recompute from scratch.

Improvements over the parent (gen004_c02):
- The 4-point check is vectorized with Python ints as bitsets: the inner
  loop over c is a single bitwise AND + test instead of a Python-level
  scan of D_b, giving O(n^3 / w) bit operations with a much lower constant.
- The check short-circuits as soon as a violation is found.
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


def _check_lb_property(graph, ordering):
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    if n == 0:
        return True

    # Build adjacency bitsets: adj_bits[v] has bit x set iff v adj x.
    adj_bits = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= (1 << v)
        adj_bits[u] = bits

    # prefix_mask[i] = bitset of vertices at positions 0..i-1.
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])

    for pb in range(n):
        b = ordering[pb]
        adj_b = adj_bits[b]

        # D_b: bitset of vertices d with pos[d] < pb and d adj b.
        D_b = 0
        for pd in range(pb):
            d = ordering[pd]
            if (adj_b >> d) & 1:
                D_b |= (1 << d)

        # mask_gt_pb = vertices at positions > pb
        mask_gt_pb = ~prefix_mask[pb + 1]

        for pa in range(pb):
            a = ordering[pa]
            if (adj_b >> a) & 1:
                continue
            adj_a = adj_bits[a]
            mask_lt_pa = prefix_mask[pa]
            # c candidates: neighbors of a at positions > pb
            c_candidates = adj_a & mask_gt_pb
            # S = D_b & mask_lt_pa: vertices d with pos[d] < pa, d adj b.
            S = D_b & mask_lt_pa
            if S == 0:
                # No d with pos[d] < pa and d adj b.
                # For any c in c_candidates, the 4-point property is violated.
                if c_candidates != 0:
                    return False
                continue
            # Check: violation iff exists c in c_candidates with
            # (S & ~adj_bits[c]) == 0, i.e. every d in S is adjacent to c.
            cc = c_candidates
            while cc:
                lsb = cc & (-cc)
                c = lsb.bit_length() - 1
                if (S & ~adj_bits[c]) == 0:
                    return False
                cc ^= lsb
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
        r1 = _check_lb_property(g, order)
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
        if not _check_lb_property(g, order):
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
    if _check_lb_property(g, [0, 1, 2]):
        raise AssertionError('self-test: regression case 1 not caught')
    # gen005_c02 failure: n=4, edges {0-1, 0-3, 1-2, 1-3, 2-3},
    # ordering [0,1,2,3] must fail
    g = [[0, 1, 0, 1], [1, 0, 1, 1], [0, 1, 0, 1], [1, 1, 1, 0]]
    if _check_lb_property(g, [0, 1, 2, 3]):
        raise AssertionError('self-test: regression case 3 not caught')
    # valid orderings must pass
    if not _check_lb_property(g, [0, 1, 3, 2]):
        raise AssertionError('self-test: valid ordering rejected')


_self_test()


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _check_lb_property(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _check_lb_property(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
