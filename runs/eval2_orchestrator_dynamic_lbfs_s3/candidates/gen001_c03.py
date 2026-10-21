"""Dynamic LexBFS ordering (candidate gen001_c03).

Strategy: maintain a valid LexBFS ordering under edge updates.

Correctness core: after any update, if the current ordering is no longer a
valid LexBFS ordering of the new graph, recompute a fresh LexBFS ordering
from scratch (O(n^2) partition-refinement).  If it is still valid, keep it.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

The check runs in O(n^2) using bitsets (Python ints as bit masks).
"""


def _lexbfs_ordering(adj, n):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).

    adj: list of lists of 0/1 (current graph).
    Returns a list of n vertices in a valid LexBFS order.
    """
    labels = [0] * n
    buckets = [[v] for v in range(n)]
    in_bucket = [True] * n
    order = []

    for v in range(n):
        b = buckets[0]
        u = b.pop(0)
        in_bucket[u] = False
        order.append(u)
        if not b:
            buckets.pop(0)
        # refine: for each bucket, split by adjacency to u
        new_buckets = []
        for bk in buckets:
            if not bk:
                continue
            nb = [x for x in bk if adj[u][x]]
            nnb = [x for x in bk if not adj[u][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        for bk in buckets:
            for x in bk:
                if adj[u][x]:
                    labels[x] |= (1 << u)
        buckets = new_buckets
    return order


def _is_valid_lexbfs(order, adj, n):
    """Check the (LB) 4-point property.

    For all a < b < c (positions in order) with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    adj_mask = [0] * n
    for v in range(n):
        m = 0
        row = adj[v]
        for u in range(n):
            if row[u]:
                m |= (1 << u)
        adj_mask[v] = m

    # pred_mask[v] = bitset of vertices with position < pos[v]
    pred_mask = [0] * n
    mask = 0
    for v in order:
        pred_mask[v] = mask
        mask |= (1 << v)

    all_mask = (1 << n) - 1

    for b in range(n):
        pb = pred_mask[b]
        nb = adj_mask[b]
        after_b = all_mask & ~pb & ~(1 << b)
        cs = nb & after_b
        while cs:
            c = (cs & -cs).bit_length() - 1
            cs &= cs - 1
            nc = adj_mask[c]
            A = pb & ~nb
            while A:
                a = (A & -A).bit_length() - 1
                A &= A - 1
                if (nb & pred_mask[a] & ~nc) == 0:
                    return False
    return True


def init(graph):
    n = len(graph)
    order = _lexbfs_ordering(graph, n)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    if _is_valid_lexbfs(order, graph, n):
        return state
    order = _lexbfs_ordering(graph, n)
    return {'ordering': order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    if _is_valid_lexbfs(order, graph, n):
        return state
    order = _lexbfs_ordering(graph, n)
    return {'ordering': order, 'n': n}
