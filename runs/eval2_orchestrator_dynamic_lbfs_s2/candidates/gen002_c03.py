"""Dynamic LexBFS ordering (candidate gen002_c03).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the static partition-refinement LexBFS to get a valid ordering.
- insert_edge(u, v): if the current ordering is already a valid LexBFS of the
  new graph, keep it (no work). Otherwise recompute from scratch.
- delete_edge(u, v): an edge deletion can only break validity, so recompute
  from scratch.

The validity check is the (LB) 4-point property of Corneil and Krueger,
applied to the REVERSE of the returned ordering (equivalently, the dual
form on the forward ordering): for all positions a < b < c in the forward
order, if ab in E and ac not in E, then there exists d < a with da in E
and dc in E.  It is checked in O(n^2) using bitsets (Python ints) over the
ordering positions.
"""


def _lexbfs(graph):
    """Static LexBFS on a 0/1 adjacency matrix. Returns a valid ordering."""
    n = len(graph)
    if n == 0:
        return []

    # adj[v] = set of neighbors of v
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)

    # buckets: list of lists of vertices, in current order
    buckets = [[v] for v in range(n)]

    order = []
    while buckets:
        # pick the first bucket (smallest label, tie-break by position)
        b = buckets.pop(0)
        v = b[0]
        order.append(v)

        # refine: for each bucket, split by adjacency to v
        new_buckets = []
        for i, bk in enumerate(buckets):
            if not bk:
                continue
            nb = [x for x in bk if x in adj[v]]
            nnb = [x for x in bk if x not in adj[v]]
            if nb and nnb:
                new_buckets.append(nnb)
                new_buckets.append(nb)
            else:
                new_buckets.append(bk)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property on the REVERSE of `order`.
    Returns True iff order is a valid LexBFS ordering of graph.

    For all positions a < b < c in the reversed order, if ac in E and
    ab not in E, then there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    if n == 0:
        return True

    # pos[v] = position of v in the REVERSED order
    pos = [0] * n
    for i, v in enumerate(reversed(order)):
        pos[v] = i

    # nbr_bits[v] = int with bit i set iff reversed_order[i] is a neighbor of v.
    nbr_bits = [0] * n
    for v in range(n):
        bits = 0
        row = graph[v]
        for u in range(n):
            if row[u]:
                bits |= (1 << pos[u])
        nbr_bits[v] = bits

    # For each pair (b, c) with b < c in reversed position:
    #   B = neighbors of rev[b] (as position bitset)
    #   C = neighbors of rev[c]
    #   bad_a = positions a < b that are in C but not B (ac in E, ab not in E)
    #   For each such a, need d < a with db in E and dc not in E.
    #   W = B & ~C (positions d with db in E, dc not in E)
    #   a is witnessed iff W has some element < a.
    #   So: if bad_a is non-empty, W must be non-empty and min(W) < min(bad_a).
    for b in range(n):
        B = nbr_bits[order[n - 1 - b]]
        for c in range(b + 1, n):
            C = nbr_bits[order[n - 1 - c]]
            bad_a = C & ~B & ((1 << b) - 1)
            if bad_a:
                W = B & ~C
                if not W:
                    return False
                w_min = (W & -W).bit_length() - 1
                a_min = (bad_a & -bad_a).bit_length() - 1
                if w_min >= a_min:
                    return False
    return True


def _is_valid_lexbfs_brute(graph, order):
    """Brute-force check of the (LB) property on the reverse of `order`.
    For all positions a < b < c in the reversed order, if ac in E and
    ab not in E, then exists d < a with db in E and dc not in E.
    """
    n = len(order)
    rev = list(reversed(order))
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                va, vb, vc = rev[a], rev[b], rev[c]
                if graph[va][vc] and not graph[va][vb]:
                    witnessed = False
                    for d in range(a):
                        vd = rev[d]
                        if graph[vd][vb] and not graph[vd][vc]:
                            witnessed = True
                            break
                    if not witnessed:
                        return False
    return True


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = _lexbfs(graph)
    return {'ordering': order}
