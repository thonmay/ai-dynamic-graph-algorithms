"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, check whether the
old ordering is still a valid LexBFS ordering via the (LB) 4-point property.
If it is, return the state unchanged (no recompute).
If not, fall back to a full O(n^2) partition-refinement LexBFS recompute.

The (LB) property (Corneil & Krueger): for all positions a < b < c in the
ordering with ac in E and ab not in E, there exists d < a with db in E and
dc not in E.  An ordering is a valid LexBFS ordering iff it satisfies (LB).

The check uses bitsets (Python ints) for adjacency rows.  For each position a,
let mask_a be the bitset of vertices in the prefix {order[0],...,order[a-1]}.
The witness condition "exists d < a with d~b and not d~c" is equivalent to
(N(b) & mask_a) not subset of (N(c) & mask_a), i.e.
(N(b) & mask_a) & ~(N(c) & mask_a) != 0.
A violation is when this is 0.
"""


def _check_lb(order, adj):
    """Check the (LB) 4-point property. Return True if valid."""
    n = len(order)
    if n <= 2:
        return True
    # Bitset of neighbors for each vertex.
    nbr = [0] * n
    for u in range(n):
        row = adj[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        nbr[u] = bits

    for a in range(n):
        va = order[a]
        # mask_a: bitset of vertices in positions [0, a)
        mask_a = 0
        for d in range(a):
            mask_a |= 1 << order[d]

        nbr_va = nbr[va]
        for b_pos in range(a + 1, n):
            vb = order[b_pos]
            if nbr_va & (1 << vb):
                continue  # ab in E, condition not triggered
            nb_a_b = nbr[vb] & mask_a
            for c_pos in range(b_pos + 1, n):
                vc = order[c_pos]
                if not (nbr_va & (1 << vc)):
                    continue  # ac not in E, condition not triggered
                nb_a_c = nbr[vc] & mask_a
                # Violation if nb_a_b is a subset of nb_a_c
                if (nb_a_b & ~nb_a_c) == 0:
                    return False
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
