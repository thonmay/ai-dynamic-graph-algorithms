"""Dynamic LexBFS ordering (candidate gen001_c03).

Strategy: maintain a valid LexBFS ordering under single-edge flips.

Correctness core: after any update, if the previously maintained ordering is
still a valid LexBFS ordering of the new graph, keep it (O(n^2) certificate
check, no recompute).  Otherwise fall back to a full static LexBFS
(partition refinement, O(n^2) on the adjacency matrix).

The certificate used is the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.  We check it in O(n^2) using
per-vertex bitsets (Python ints) of the prefix of the ordering.

The "keep if still valid" fast path is sound: a LexBFS ordering is defined
as any ordering satisfying the (LB) property, and the property depends only
on the current graph and the ordering, not on how the ordering was
produced.  So if the old ordering still satisfies it, it is a legal answer.
"""


def _lexbfs_full(adj):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).

    Returns an ordering (list of vertices) that is a valid LexBFS ordering
    of the graph given by the 0/1 adjacency matrix `adj`.
    """
    n = len(adj)
    if n == 0:
        return []

    # Buckets of unprocessed vertices, all vertices in a bucket share the
    # same label (tuple of 0/1 bits = adjacency to the ordered prefix).
    buckets = [[v for v in range(n)]]
    bucket_labels = [()]

    ordering = []
    unprocessed = n

    while unprocessed > 0:
        # pick the first vertex of the first bucket
        v = buckets[0][0]
        buckets[0].pop(0)
        if not buckets[0]:
            buckets.pop(0)
            bucket_labels.pop(0)
        ordering.append(v)
        unprocessed -= 1

        # refine every bucket by adjacency to v
        new_buckets = []
        new_labels = []
        for b, lab in zip(buckets, bucket_labels):
            if not b:
                continue
            b0 = [x for x in b if adj[v][x]]
            b1 = [x for x in b if not adj[v][x]]
            if b0:
                new_buckets.append(b0)
                new_labels.append(lab + (1,))
            if b1:
                new_buckets.append(b1)
                new_labels.append(lab + (0,))
        buckets = new_buckets
        bucket_labels = new_labels

    return ordering


def _is_valid_lexbfs(adj, ordering):
    """Check the (LB) 4-point property in O(n^2) using bitsets.

    For positions a < b < c with ac in E and ab not in E, we need some
    d < a with db in E and dc not in E.

    For each pair (b, c) of positions with b < c and bc not in E, let
    S = { a < b : ac in E }.  The property requires: for every a in S,
    exists d < a with db in E and dc not in E.  The predicate
    ok(a) = ( {d < a : db in E} intersects {d < a : dc not in E} ) is
    monotone non-decreasing in a (the prefix sets only grow), so it
    suffices to check ok at the smallest a in S.

    So: for each pair (b, c), b < c, bc not in E:
        let a0 = smallest position a < b with ordering[a] adjacent to c.
        If no such a0 exists, the pair imposes no constraint.
        Otherwise check: exists d < a0 with d adjacent to b and d not
        adjacent to c.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # adj_bits[v] = bitset of neighbors of v
    adj_bits = [0] * n
    for v in range(n):
        row = adj[v]
        bits = 0
        for u in range(n):
            if row[u]:
                bits |= (1 << u)
        adj_bits[v] = bits

    # pref[i] = bitset of vertices d with pos[d] < i
    pref = [0] * (n + 1)
    for i in range(n):
        pref[i + 1] = pref[i] | (1 << ordering[i])

    # For each c, scan b in increasing position order, maintaining
    # first = smallest position a < b with ordering[a] adjacent to c.
    for c in range(n):
        first = -1
        for b in range(n):
            if first != -1 and b < c and not adj[ordering[b]][c]:
                b_v = ordering[b]
                mask = pref[first]  # vertices d with pos[d] < first
                if (mask & adj_bits[b_v] & ~adj_bits[c]) == 0:
                    return False
            if first == -1 and adj[ordering[b]][c]:
                first = b
    return True


def _check_lb_direct(adj, ordering):
    """Direct O(n^4) check of the (LB) 4-point property (reference)."""
    n = len(ordering)
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                va, vb, vc = ordering[a], ordering[b], ordering[c]
                if adj[va][vc] and not adj[va][vb]:
                    ok = False
                    for d in range(a):
                        vd = ordering[d]
                        if adj[vd][vb] and not adj[vd][vc]:
                            ok = True
                            break
                    if not ok:
                        return False
    return True


def _check_lb_direct(adj, ordering):
    """Direct O(n^4) check of the (LB) 4-point property (reference)."""
    n = len(ordering)
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                va, vb, vc = ordering[a], ordering[b], ordering[c]
                if adj[va][vc] and not adj[va][vb]:
                    ok = False
                    for d in range(a):
                        vd = ordering[d]
                        if adj[vd][vb] and not adj[vd][vc]:
                            ok = True
                            break
                    if not ok:
                        return False
    return True


def init(graph):
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _check_lb_direct(graph, ordering):
        return state
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _check_lb_direct(graph, ordering):
        return state
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering}
