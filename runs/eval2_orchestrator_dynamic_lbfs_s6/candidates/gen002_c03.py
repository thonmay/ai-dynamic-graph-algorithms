"""Dynamic LexBFS ordering (candidate gen002_c03).

Strategy: maintain a valid LexBFS ordering under edge updates.

Correctness core: after any update, if the previously maintained ordering
is no longer a valid LexBFS ordering of the new graph, recompute a fresh
LexBFS ordering from scratch using the standard partition-refinement
algorithm (Habib-McConnell-Paul-Viennot style, O(n+m)).

Dynamic fast path: after an update, first check whether the old ordering
is still valid via the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.  The check is done in O(n^2) using
bitsets (Python ints as bitsets) over the ordering positions.  If the
old ordering is still valid, we keep it and skip the recompute.
"""


def _lexbfs_ordering(adj, n):
    """Compute a valid LexBFS ordering of the undirected graph adj (0/1 matrix).

    Returns a list of n vertex ids.  Uses the partition-refinement
    algorithm: maintain a queue of buckets (lists of vertices) and a
    label (bitmask of already-processed vertices) per vertex.  When a
    bucket is refined by a vertex v, the sub-bucket of vertices adjacent
    to v is moved to the front of the queue.
    """
    # adj_bits[u] = bitmask of neighbors of u
    adj_bits = [0] * n
    for u in range(n):
        row = adj[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        adj_bits[u] = bits

    # buckets: list of lists of vertices, in queue order
    buckets = [[u] for u in range(n)]
    # queue of bucket indices
    from collections import deque
    q = deque(range(n))

    order = []
    while q:
        bi = q.popleft()
        bucket = buckets[bi]
        if not bucket:
            continue
        # pick the first vertex in the bucket
        v = bucket[0]
        order.append(v)
        # remove v from its bucket
        bucket.pop(0)
        # refine every bucket that still has vertices, using v
        # We refine all buckets from index bi onward (including the
        # remainder of the current bucket).
        for j in range(bi, len(buckets)):
            b = buckets[j]
            if not b:
                continue
            # split b into those adjacent to v and those not
            front = []
            back = []
            for x in b:
                if (adj_bits[v] >> x) & 1:
                    front.append(x)
                else:
                    back.append(x)
            if front and back:
                # replace bucket j with back, insert front at front of queue
                buckets[j] = back
                q.appendleft(len(buckets))
                buckets.append(front)
            elif front:
                # all adjacent: bucket unchanged
                pass
    return order


def _is_valid_lexbfs(order, adj, n):
    """Check the (LB) 4-point property of Corneil and Krueger.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True iff the ordering is a valid LexBFS ordering.
    """
    # Build position-based neighbor bitmasks
    # pos_nbr[i] = bitmask of positions j such that order[i]~order[j]
    pos_nbr = [0] * n
    for i in range(n):
        u = order[i]
        bits = 0
        for j in range(n):
            if i != j and adj[u][order[j]]:
                bits |= 1 << j
        pos_nbr[i] = bits

    # For each c, iterate b from 0 to c-1:
    #   A = {a < b : P[a]~P[c]}  (bitmask over positions)
    #   If P[b] not adjacent to P[c] and A is non-empty:
    #     For EVERY a in A, require: exists d < a with P[d]~P[b]
    #     and not P[d]~P[c], i.e.
    #       (pos_nbr[b] & ((1 << a) - 1)) & not_nbr_c != 0
    #   where not_nbr_c = complement of pos_nbr[c] masked to n bits.
    #
    # Note: checking only the minimum a in A is NOT sufficient -- the
    # witness condition is monotone in a (larger a admits a superset of
    # candidate d's), so a larger a can have a witness even when the
    # minimum a does not.  We therefore iterate over all a in A.

    # For each c, iterate b from 0 to c-1:
    #   A = {a < b : P[a]~P[c]}  (bitmask over positions)
    #   If P[b] not adjacent to P[c] and A is non-empty:
    #     For EVERY a in A, require: exists d < a with P[d]~P[b]
    #     and not P[d]~P[c], i.e.
    #       (pos_nbr[b] & ((1 << a) - 1)) & not_nbr_c != 0
    #   where not_nbr_c = complement of pos_nbr[c] masked to n bits.
    #
    # Note: checking only the minimum a in A is NOT sufficient -- the
    # witness condition is monotone in a (larger a admits a superset of
    # candidate d's), so a larger a can have a witness even when the
    # minimum a does not.  We therefore iterate over all a in A.

    full_mask = (1 << n) - 1
    for c in range(n):
        not_nbr_c = full_mask ^ pos_nbr[c]
        for b in range(c):
            if (pos_nbr[b] >> c) & 1:
                # P[b] adjacent to P[c]: no constraint for this (b, c)
                continue
            # P[b] not adjacent to P[c]
            A = pos_nbr[c] & ((1 << b) - 1)
            if A == 0:
                continue
            # For every a in A, check the witness condition
            nbr_b = pos_nbr[b]
            a_bits = A
            while a_bits:
                low = a_bits & (-a_bits)
                # a = position of low; (1 << a) - 1 == low - 1
                if ((nbr_b & (low - 1)) & not_nbr_c) == 0:
                    return False
                a_bits ^= low
    return True


def _recompute(adj, n):
    """Recompute a fresh LexBFS ordering."""
    return _lexbfs_ordering(adj, n)


def init(graph):
    n = len(graph)
    order = _lexbfs_ordering(graph, n)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    # Check if the old ordering is still valid
    if _is_valid_lexbfs(order, graph, n):
        return state
    # Otherwise recompute
    new_order = _recompute(graph, n)
    return {'ordering': new_order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    # Check if the old ordering is still valid
    if _is_valid_lexbfs(order, graph, n):
        return state
    # Otherwise recompute
    new_order = _recompute(graph, n)
    return {'ordering': new_order, 'n': n}
