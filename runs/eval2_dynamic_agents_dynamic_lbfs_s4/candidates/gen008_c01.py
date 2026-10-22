"""Dynamic LexBFS ordering (candidate gen008_c01).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge / delete_edge: after the update, check the (LB) 4-point
  property of Corneil and Krueger on the current ordering.  If it still
  holds, the ordering is still a valid LexBFS and we keep it (no recompute).
  Otherwise we recompute from scratch.

Key optimization over the parent: the 4-point check after a single edge
flip (u, v) is targeted.  A triple (a, b, c) with a < b < c can only be
affected if the flipped edge is one of ab, ac, or dc (for some d < a).
This means:
  - b must be u or v (since ab is the flipped edge), OR
  - a must be u or v (since ac is the flipped edge), OR
  - c must be u or v (since dc is the flipped edge).
So we only need to check triples where at least one of a, b, c is u or v.
This reduces the check from O(n^3) to O(n^2) in the common case.

The full bitset checker is kept as a fallback (used only when the targeted
check finds a violation, to confirm before recomputing).

The checker is verified against a brute-force reference on small random
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


def _check_lb_targeted(graph, ordering, u, v):
    """Targeted check of the (LB) 4-point property after flipping edge (u, v).

    Only triples (a, b, c) with a < b < c where at least one of a, b, c
    is u or v can be affected by the edge flip.  We check exactly those
    triples in O(n^2) time.

    Returns True if no violation is found among the affected triples.
    """
    n = len(ordering)
    if n == 0:
        return True

    # Build position map: pos[vertex] = position in ordering
    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    # Build adjacency bitsets
    adj_bits = [0] * n
    for vtx in range(n):
        row = graph[vtx]
        bits = 0
        for w in range(n):
            if row[w]:
                bits |= (1 << w)
        adj_bits[vtx] = bits

    # prefix_mask[i] = bitset of vertices at positions 0..i-1.
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])

    # The affected triples are those where b in {u,v} or a in {u,v} or c in {u,v}.
    # We iterate over all (pa, pb) pairs where ordering[pa] or ordering[pb] is u or v,
    # and check all c > pb.

    # Precompute D_b for b = u and b = v (and any other b we need)
    # Actually, let's just iterate over the relevant (pa, pb) pairs.

    # Case 1: b is u or v
    for b in (u, v):
        pb = pos[b]
        adj_b = adj_bits[b]
        # D_b: bitset of vertices d with pos[d] < pb and d adj b.
        D_b = 0
        for pd in range(pb):
            d = ordering[pd]
            if (adj_b >> d) & 1:
                D_b |= (1 << d)
        mask_gt_pb = ~prefix_mask[pb + 1]
        for pa in range(pb):
            a = ordering[pa]
            if (adj_b >> a) & 1:
                continue
            adj_a = adj_bits[a]
            mask_lt_pa = prefix_mask[pa]
            c_candidates = adj_a & mask_gt_pb
            S = D_b & mask_lt_pa
            if S == 0:
                if c_candidates != 0:
                    return False
                continue
            cc = c_candidates
            while cc:
                lsb = cc & (-cc)
                c = lsb.bit_length() - 1
                if (S & ~adj_bits[c]) == 0:
                    return False
                cc ^= lsb

    # Case 2: a is u or v (and b is NOT u or v, to avoid double-counting)
    for a in (u, v):
        pa = pos[a]
        adj_a = adj_bits[a]
        for pb in range(pa + 1, n):
            b = ordering[pb]
            if b == u or b == v:
                continue  # already handled in Case 1
            if (adj_a >> b) & 1:
                continue  # ab in E: condition not met
            adj_b = adj_bits[b]
            # D_b: bitset of vertices d with pos[d] < pb and d adj b.
            D_b = 0
            for pd in range(pb):
                d = ordering[pd]
                if (adj_b >> d) & 1:
                    D_b |= (1 << d)
            mask_gt_pb = ~prefix_mask[pb + 1]
            mask_lt_pa = prefix_mask[pa]
            c_candidates = adj_a & mask_gt_pb
            S = D_b & mask_lt_pa
            if S == 0:
                if c_candidates != 0:
                    return False
                continue
            cc = c_candidates
            while cc:
                lsb = cc & (-cc)
                c = lsb.bit_length() - 1
                if (S & ~adj_bits[c]) == 0:
                    return False
                cc ^= lsb

    # Case 3: c is u or v (and a, b are NOT u or v, to avoid double-counting)
    for c in (u, v):
        pc = pos[c]
        adj_c = adj_bits[c]
        for pa in range(pc):
            a = ordering[pa]
            if a == u or a == v:
                continue  # already handled in Case 2
            adj_a = adj_bits[a]
            if not (adj_a >> c) & 1:
                continue  # ac not in E: condition not met
            for pb in range(pa + 1, pc):
                b = ordering[pb]
                if b == u or b == v:
                    continue  # already handled in Case 1
                if (adj_a >> b) & 1:
                    continue  # ab in E: condition not met
                # Need: exists d < a with db in E and dc not in E
                adj_b = adj_bits[b]
                # S = {d : pos[d] < pa, d adj b}
                # Violation iff for all d in S, d adj c (i.e. S & ~adj_c == 0)
                # AND S is non-empty... wait, no.
                # The condition is: exists d < a with db in E and dc not in E.
                # Violation: for all d < a, either db not in E or dc in E.
                # i.e. (D_b & mask_lt_pa) & ~adj_c == 0
                # where D_b = {d : pos[d] < pb, d adj b}
                # But we need d < a, i.e. pos[d] < pa.
                # S = {d : pos[d] < pa, d adj b}
                # Violation iff S & ~adj_c == 0
                # But wait: if S is empty, then there's no d < a with db in E,
                # so the condition "exists d < a with db in E and dc not in E" is
                # vacuously... no, it's not vacuously true. If S is empty,
                # there is no d < a with db in E, so the condition fails.
                # Actually wait: the condition is "there exists d < a with
                # db in E and dc not in E". If S is empty (no d < a adjacent to b),
                # then the condition is NOT satisfied, so it's a violation.
                # Hmm, but that's the same as S & ~adj_c == 0 when S is empty.
                # Yes: if S is empty, S & ~adj_c = 0, so we'd flag a violation.
                # That's correct.
                mask_lt_pa = prefix_mask[pa]
                # S = {d : pos[d] < pa, d adj b}
                # We need to compute this.
                S = 0
                for pd in range(pa):
                    d = ordering[pd]
                    if (adj_b >> d) & 1:
                        S |= (1 << d)
                if (S & ~adj_c) == 0:
                    return False

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

    # Test the targeted checker against the full checker
    for trial in range(500):
        n = rng.randint(2, 8)
        g = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < 0.4:
                    g[u][v] = 1
                    g[v][u] = 1
        order = _lexbfs(g)
        # Pick a random edge to flip
        u = rng.randint(0, n - 1)
        v = rng.randint(0, n - 1)
        if u == v:
            continue
        # Flip the edge
        g[u][v] ^= 1
        g[v][u] ^= 1
        r_full = _check_lb_property(g, order)
        r_targeted = _check_lb_targeted(g, order, u, v)
        if r_full != r_targeted:
            raise AssertionError(
                'self-test targeted mismatch: n=%d g=%s order=%s edge=(%d,%d) '
                'full=%s targeted=%s'
                % (n, g, order, u, v, r_full, r_targeted))
        # Flip back
        g[u][v] ^= 1
        g[v][u] ^= 1


_self_test()


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    u, v = edge
    if _check_lb_targeted(graph, ordering, u, v):
        return state
    # Targeted check found a violation; confirm with full check
    if _check_lb_property(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    u, v = edge
    if _check_lb_targeted(graph, ordering, u, v):
        return state
    # Targeted check found a violation; confirm with full check
    if _check_lb_property(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
