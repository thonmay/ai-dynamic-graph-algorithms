"""Dynamic LexBFS ordering (candidate gen005_c02).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge / delete_edge: after the update, check the (LB) 4-point
  property of Corneil and Krueger on the current ordering.  If it still
  holds, the ordering is still a valid LexBFS and we keep it (no recompute).
  Otherwise we recompute from scratch.

Improvements over the parent (gen004_c02):
- The 4-point check is vectorized with Python ints as bitsets.  The inner
  loop over c is a single bitwise AND + test instead of a Python-level
  scan of D_b, giving O(n^3 / w) bit operations with a much lower constant.
- The check short-circuits as soon as a violation is found.
"""


def _lexbfs(graph):
    """Static partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sorted lists; a vertex is in exactly one bucket
    # order of buckets = order in which they were last refined
    buckets = [list(range(n))]
    bkt_of = [0] * n
    pos_in_bucket = list(range(n))

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
        pos_in_bucket[v] = -1
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
        for i, b in enumerate(buckets):
            for j, x in enumerate(b):
                bkt_of[x] = i
                pos_in_bucket[x] = j

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
            # Check: exists c in c_candidates with (S & ~adj_bits[c]) != 0.
            cc = c_candidates
            while cc:
                lsb = cc & (-cc)
                c = lsb.bit_length() - 1
                if (S & ~adj_bits[c]) != 0:
                    return False
                cc ^= lsb
    return True


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
