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

Improvements over the parent:
- The neighbor bitsets are cached in the state and updated incrementally on
  each edge flip (O(1) per update) instead of being rebuilt from the matrix
  on every update.
- The prefix mask in the check is built incrementally (O(n) total) instead of
  being rebuilt per position a (O(n^2)).
- The check is restructured: for each position a, we scan the suffix from
  right to left, maintaining the set of N(c)&P values for neighbors of a
  seen so far. For each non-neighbor b of a, we check if any seen N(c)&P
  is a superset of N(b)&P. This avoids the inner c-loop for each b.
"""


def _build_nbr(adj):
    """Build the list of neighbor bitsets from the adjacency matrix."""
    n = len(adj)
    nbr = [0] * n
    for u in range(n):
        row = adj[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        nbr[u] = bits
    return nbr


def _check_lb(order, nbr):
    """Check the (LB) 4-point property. Return True if valid.

    For each position a, we need: for all b_pos > a with a NOT adjacent to
    order[b_pos], and c_pos > b_pos with a adjacent to order[c_pos], there
    exists d < a with d adjacent to order[b_pos] and d NOT adjacent to
    order[c_pos].

    Equivalently: for each a, let P = prefix mask before a.
    For each b in suffix after a with a NOT adjacent to b:
        For each c in suffix after b with a adjacent to c:
            (N(b) & P) must NOT be a subset of (N(c) & P).

    Restructured: for fixed a, scan positions from right to left.
    Maintain a list of S_c = N(c) & P for neighbors c of a seen so far.
    For each non-neighbor b of a, check if any S_c in the list is a
    superset of S_b = N(b) & P. If so, violation.
    """
    n = len(order)
    if n <= 2:
        return True

    mask_a = 0
    for a in range(n):
        va = order[a]
        nbr_va = nbr[va]
        # Scan suffix from right to left
        # seen_sc: list of N(c) & mask_a for neighbors c of va seen so far
        seen_sc = []
        for pos in range(n - 1, a, -1):
            v = order[pos]
            if nbr_va & (1 << v):
                # v is a neighbor of va; add its S value
                seen_sc.append(nbr[v] & mask_a)
            else:
                # v is a non-neighbor of va; check if any seen S_c is a
                # superset of S_v
                sv = nbr[v] & mask_a
                if sv == 0:
                    # S_v is empty, so S_v is a subset of any S_c
                    # (including the empty set). But we need c to exist.
                    # If seen_sc is non-empty, violation.
                    if seen_sc:
                        return False
                    # If seen_sc is empty, no c exists, no violation.
                    continue
                # Check if any S_c in seen_sc is a superset of sv
                # i.e., sv & ~S_c == 0 for some S_c
                for sc in seen_sc:
                    if (sv & ~sc) == 0:
                        return False
        mask_a |= 1 << va
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
    return {'ordering': order, 'n': n, 'nbr': _build_nbr(graph)}


def insert_edge(graph, edge, state):
    u, v = edge
    nbr = state['nbr']
    # The edge is now present in the graph; make sure the bitsets reflect it.
    nbr[u] |= 1 << v
    nbr[v] |= 1 << u
    order = state['ordering']
    if _check_lb(order, nbr):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph), 'nbr': nbr}


def delete_edge(graph, edge, state):
    u, v = edge
    nbr = state['nbr']
    # The edge is now absent from the graph; make sure the bitsets reflect it.
    nbr[u] &= ~(1 << v)
    nbr[v] &= ~(1 << u)
    order = state['ordering']
    if _check_lb(order, nbr):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph), 'nbr': nbr}
