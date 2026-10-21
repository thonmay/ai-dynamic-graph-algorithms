"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, check whether the
old ordering is still a valid LexBFS ordering via the (LB) 4-point property.
If it is, return the state unchanged (no recompute).
If not, fall back to a full O(n^2) partition-refinement LexBFS recompute.

The (LB) property (Corneil & Krueger): for all positions a < b < c in the
ordering with ac in E and ab not in E, there exists d < a with db in E and
dc not in E.  An ordering is a valid LexBFS ordering iff it satisfies (LB).

Optimizations over the naive O(n^4) check:
- Bitset adjacency (Python ints) for O(1) edge tests.
- For each position a, precompute the set of d < a that are adjacent to
  order[b] (as a bitset over positions).  Then for a candidate c, the
  witness d must lie in (adj_d_to_b) & (NOT adj_d_to_c), restricted to
  positions < a.  This is a single bitset AND + mask + test.
"""


def _check_lb(order, adj):
    """Check the (LB) 4-point property. Return True if valid."""
    n = len(order)
    if n <= 2:
        return True
    # pos[v] = position of v in the ordering
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    # nbr_bits[v] = bitset of neighbors of v (over vertex ids)
    nbr_bits = [0] * n
    for u in range(n):
        row = adj[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= (1 << v)
        nbr_bits[u] = bits
    # pos_nbr[v] = bitset of positions of neighbors of v
    pos_nbr = [0] * n
    for v in range(n):
        bits = 0
        nb = nbr_bits[v]
        while nb:
            lsb = nb & (-nb)
            u = lsb.bit_length() - 1
            bits |= (1 << pos[u])
            nb ^= lsb
        pos_nbr[v] = bits
    # pos_not_nbr[v] = bitset of positions of NON-neighbors of v
    # (includes v itself, which is fine: v is never in the d < a range
    #  when v == order[b] or order[c] since b, c > a)
    pos_not_nbr = [0] * n
    for v in range(n):
        pos_not_nbr[v] = ((1 << n) - 1) ^ pos_nbr[v]
    # mask_lt[a] = (1 << a) - 1 : positions < a
    for a in range(n):
        va = order[a]
        mask = (1 << a) - 1
        if mask == 0:
            # a = 0: no d < a exists, so ANY triggered triple (a=0, b, c
            # with ab not in E and ac in E) violates (LB).
            for b in range(1, n):
                vb = order[b]
                if (nbr_bits[va] >> vb) & 1:
                    continue  # ab in E
                if pos_nbr[va] & (~((1 << (b + 1)) - 1)):
                    return False
            continue
        # For each b > a with ab not in E:
        #   for each c > b with ac in E: need d < a with db in E, dc not in E
        # Precompute for this a: for each b, adj_d_to_b = pos_nbr[order[b]] & mask
        # Then for c: witness set = adj_d_to_b & ~pos_nbr[order[c]] & mask
        # We can iterate b, then c.
        # To speed up: for fixed a, the set of c with ac in E is pos_nbr[va] & (positions > b).
        # Iterate b from a+1 to n-1:
        for b in range(a + 1, n):
            vb = order[b]
            if (nbr_bits[va] >> vb) & 1:
                continue  # ab in E
            adj_d_to_b = pos_nbr[vb] & mask
            if adj_d_to_b == 0:
                # No d < a adjacent to b; any c > b with ac in E fails.
                # Check if there is any c > b with ac in E.
                if pos_nbr[va] & (~((1 << (b + 1)) - 1)):
                    return False
                continue
            # For each c > b with ac in E:
            c_bits = pos_nbr[va] & (~((1 << (b + 1)) - 1))
            while c_bits:
                lsb = c_bits & (-c_bits)
                c = lsb.bit_length() - 1
                vc = order[c]
                # witness d in adj_d_to_b & pos_not_nbr[vc]
                if not (adj_d_to_b & pos_not_nbr[vc]):
                    return False
                c_bits ^= lsb
    return True


def _lexbfs_full(adj):
    """Full O(n^2) LexBFS via partition refinement. Returns ordering list."""
    n = len(adj)
    if n == 0:
        return []
    # buckets: list of lists of vertices with the same label so far
    buckets = [[v for v in range(n)]]
    order = []

    while buckets:
        # pick first vertex of first bucket
        v = buckets[0][0]
        buckets[0].pop(0)
        if not buckets[0]:
            buckets.pop(0)
        order.append(v)
        # refine all remaining buckets by adjacency to v
        new_buckets = []
        for b in buckets:
            b1 = [x for x in b if adj[v][x]]
            b0 = [x for x in b if not adj[v][x]]
            if b1:
                new_buckets.append(b1)
            if b0:
                new_buckets.append(b0)
        buckets = new_buckets

    return order


def init(graph):
    n = len(graph)
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _check_lb(order, graph):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph)}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _check_lb(order, graph):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph)}
