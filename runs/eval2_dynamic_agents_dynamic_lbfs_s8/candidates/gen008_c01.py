"""Dynamic LexBFS ordering.

Maintains a valid LexBFS ordering under edge insertions and deletions.

On each update we verify the maintained ordering against the (LB) 4-point
property of Corneil and Krueger:

    for all a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

If the property still holds, the ordering is a valid LexBFS and we keep it
(cheap path). Otherwise we recompute a fresh LexBFS ordering with the
partition-refinement algorithm of Habib, McConnell, Paul and Viennot
(O(n^2) on the adjacency matrix).

The 4-point check is accelerated with bitsets (Python ints as bit vectors):
for each vertex v we precompute N[v] (neighbors) and Z[v] (non-neighbors)
as ints, and for each position i we precompute P[i] = union of N[order[t]]
for t < i.  The witness test for (a, b, c) at positions i < j < k becomes
the single bit test  (P[i] & N[b] & Z[c]) != 0.
"""


def _lexbfs(g):
    """Static partition-refinement LexBFS on adjacency matrix g.

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(g)
    if n == 0:
        return []
    # buckets: list of lists of vertices; all vertices in a bucket share
    # the same label.
    buckets = [list(range(n))]
    order = []
    while buckets:
        # take the first bucket, pick its first vertex
        b = buckets[0]
        v = b[0]
        order.append(v)
        b.pop(0)
        if not b:
            buckets.pop(0)
        # refine every remaining bucket by adjacency to v: neighbors
        # (label extended with the marker) come before non-neighbors.
        new_buckets = []
        for bucket in buckets:
            nb = []
            non_nb = []
            for w in bucket:
                if g[v][w]:
                    nb.append(w)
                else:
                    non_nb.append(w)
            if nb:
                new_buckets.append(nb)
            if non_nb:
                new_buckets.append(non_nb)
        buckets = new_buckets
    return order


def _is_lexbfs(g, order):
    """Check the (LB) 4-point property for `order` on graph g.

    For all a<b<c with ac in E and ab not in E, there must exist d<a with
    db in E and dc not in E.  Bitset-accelerated: O(n^3 / word) bit ops.
    """
    n = len(order)
    N = [0] * n
    Z = [0] * n
    for v in range(n):
        row = g[v]
        bits = 0
        for w in range(n):
            if row[w]:
                bits |= 1 << w
        N[v] = bits
        Z[v] = bits ^ ((1 << n) - 1)
    # P[i] = union of N[order[t]] for t < i
    P = [0] * n
    acc = 0
    for i in range(n):
        P[i] = acc
        acc |= N[order[i]]
    for i in range(n):
        a = order[i]
        na = N[a]
        for j in range(i + 1, n):
            b = order[j]
            if (na >> b) & 1:
                continue  # need ab not in E
            nb = N[b]
            for k in range(j + 1, n):
                c = order[k]
                if not ((na >> c) & 1):
                    continue  # need ac in E
                if not (P[i] & nb & Z[c]):
                    return False
    return True


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    # An insertion can create new 4-point obligations (new edge ac with
    # a<b<c, ab not in E) that the old ordering may not satisfy, so we
    # cannot keep the old ordering blindly.  Verify the (LB) property on
    # the updated graph; keep the ordering if it still holds, otherwise
    # recompute.
    order = state['ordering']
    if _is_lexbfs(graph, order):
        return state
    return {'ordering': _lexbfs(graph)}


def delete_edge(graph, edge, state):
    # A deletion can only destroy witnesses, so the property can only be
    # hurt.  Verify the (LB) property; recompute if it fails.
    order = state['ordering']
    if _is_lexbfs(graph, order):
        return state
    return {'ordering': _lexbfs(graph)}
