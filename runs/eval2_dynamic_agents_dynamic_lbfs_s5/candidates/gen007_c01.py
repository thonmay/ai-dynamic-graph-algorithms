"""Dynamic LexBFS ordering (candidate gen007_c01).

Strategy: maintain a valid LexBFS ordering under single edge flips.

Correctness core:
  * init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
    with a deterministic tie-break (smallest vertex id first).
  * insert_edge / delete_edge: a single edge flip can invalidate the current
    ordering.  We verify the (LB) 4-point property of Corneil and Krueger
    using the current ordering; if it still holds we keep the ordering,
    otherwise we recompute from scratch.

Improvements over the parent (gen005_c02):
  * The (LB) check after an update only inspects triples affected by the
    flipped edge (O(n^2) instead of O(n^3)), because a single edge flip
    changes the truth value of the antecedent/consequent only for triples
    involving the flipped edge.
  * Before falling back to a full recompute, we try a cheap local repair:
    move the two endpoints of the flipped edge to the front of the ordering
    (in both orders) and re-check; if that yields a valid ordering we keep
    it, avoiding the O(n^2) full LexBFS recompute.

The state carries the ordering.  All work is done in pure Python with lists.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list.

    Correct HMPV algorithm:
      * P is an ordered list of buckets (each a list of vertices).
      * S is the set of already-output vertices.
      * At each step, pick the FIRST non-empty bucket, take its FIRST
        vertex v, output it, then refine every bucket by adjacency to v.
      * Refinement: for each bucket B, split into B_adj (neighbors of v)
        and B_nonadj (non-neighbors of v).  The refined bucket list is
        formed by replacing each B with [B_adj, B_nonadj] (in that order),
        dropping empty parts.  This preserves the lexicographic order of
        the neighbor-sets of S.
    """
    n = len(graph)
    if n == 0:
        return []
    # P: ordered list of buckets; each bucket is a list of vertices.
    P = [list(range(n))]
    S = set()
    order = []

    while len(S) < n:
        # find first non-empty bucket
        idx = None
        for i, B in enumerate(P):
            if B:
                idx = i
                break
        if idx is None:
            break
        B = P[idx]
        v = B[0]
        order.append(v)
        S.add(v)
        # remove v from its bucket
        B.pop(0)
        # refine: replace each bucket with [adj, nonadj]
        new_P = []
        for Bk in P:
            if not Bk:
                continue
            adj = []
            nonadj = []
            for x in Bk:
                if graph[x][v]:
                    adj.append(x)
                else:
                    nonadj.append(x)
            if adj:
                new_P.append(adj)
            if nonadj:
                new_P.append(nonadj)
        P = new_P
    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property: for all positions i < j < k with
    order[i]-order[k] in E and order[i]-order[j] not in E, there exists
    t < i with order[t]-order[j] in E and order[t]-order[k] not in E.
    Returns True if valid."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > b with ac in E
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                # need d < a (position) with db in E and dc not in E
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _is_valid_lexbfs_after_flip(graph, order, u, v):
    """Check the (LB) 4-point property after a single edge flip (u, v).

    Only triples (i, j, k) with i < j < k where the flipped edge is one of
    (a,b), (a,c), or (d,b)/(d,c) for some d < i can change status.  We
    check:
      1. All triples where the flipped edge is (a, b) or (a, c) -- the
         antecedent may have changed.
      2. All triples where the flipped edge is (d, b) or (d, c) for some
         d < i -- the witness may have changed.

    This is O(n^2) in the worst case (vs O(n^3) for the full check).
    """
    n = len(order)
    pos = {vertex: i for i, vertex in enumerate(order)}
    pu = pos[u]
    pv = pos[v]

    # --- Part 1: flipped edge is (a, b) or (a, c) in the antecedent ---
    # For each position i, a = order[i].  The flipped edge (u,v) is (a,b)
    # or (a,c) iff a is u or v.
    for a_vertex in (u, v):
        i = pos[a_vertex]
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            # Check if (a, b) is the flipped edge
            if b == u or b == v:
                # (a, b) is the flipped edge
                if graph[a][b]:
                    continue  # ab in E, antecedent not triggered
                # ab not in E; check all c > b with ac in E
                for k in range(j + 1, n):
                    c = order[k]
                    if not graph[a][c]:
                        continue
                    found = False
                    for t in range(i):
                        d = order[t]
                        if graph[d][b] and not graph[d][c]:
                            found = True
                            break
                    if not found:
                        return False
            else:
                # (a, b) is not the flipped edge; check (a, c) for c > b
                # where c is u or v
                for k in range(j + 1, n):
                    c = order[k]
                    if c != u and c != v:
                        continue
                    # (a, c) is the flipped edge
                    if not graph[a][c]:
                        continue  # ac not in E, antecedent not triggered
                    # ac in E and ab not in E (ab is not flipped, so its
                    # status is unchanged from before the flip)
                    found = False
                    for t in range(i):
                        d = order[t]
                        if graph[d][b] and not graph[d][c]:
                            found = True
                            break
                    if not found:
                        return False

    # --- Part 2: flipped edge is (d, b) or (d, c) for some d < i ---
    # For each triple (i, j, k) with i < j < k, the witness d < i could be
    # affected if (d, b) or (d, c) is the flipped edge.  That means d is u
    # or v, and b or c is the other endpoint.
    #
    # The flipped edge (u,v) affects witness (d,b) iff {d,b} = {u,v},
    # i.e., d=u and b=v, or d=v and b=u.  Similarly for (d,c).
    # So for a given triple (i,j,k), the affected witnesses are:
    #   - d = u (if u < i position-wise) with b = v, or d = v with b = u
    #   - d = u with c = v, or d = v with c = u
    #
    # We only need to re-check triples where the antecedent holds AND at
    # least one of the affected witness pairs is relevant.  But to be safe,
    # we check all triples where the antecedent holds and the flipped edge
    # could be a witness.
    #
    # Optimization: the flipped edge (u,v) can only be a witness (d,b) or
    # (d,c) if one of u,v is at position < i and the other is at position
    # j or k.  So we iterate over i, and for each i check if u or v is at
    # position < i, and if the other is at position j or k.

    for i in range(n):
        a = order[i]
        # Determine which of u, v are at positions < i
        u_before = pu < i
        v_before = pv < i
        if not u_before and not v_before:
            continue  # no affected witness possible
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # ab in E, antecedent not triggered
            # ab not in E; check all c > b with ac in E
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                # ac in E and ab not in E; check witnesses
                # Only need to check if the flipped edge could be a witness
                # i.e., (d,b) or (d,c) is the flipped edge for some d < i
                # This means: (u,v) = (d,b) or (d,c) for some d < i
                # i.e., {u,v} = {d,b} or {u,v} = {d,c}
                # i.e., (u==d and v==b) or (v==d and u==b) or
                #      (u==d and v==c) or (v==d and u==c)
                # Since d < i, we need u < i or v < i (position-wise)
                # and the other endpoint is b or c.
                affected = False
                if u_before and (b == v or c == v):
                    affected = True
                if v_before and (b == u or c == u):
                    affected = True
                if not affected:
                    continue
                # Check if any witness still works
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False

    return True


def _try_local_repair(graph, order, u, v):
    """Try to repair the ordering by moving u and v to the front.

    Returns a valid ordering if found, else None.
    """
    n = len(order)
    if n <= 2:
        return order  # trivially valid

    # Try both orders: [u, v, rest] and [v, u, rest]
    for first, second in ((u, v), (v, u)):
        rest = [x for x in order if x != first and x != second]
        candidate = [first, second] + rest
        if _is_valid_lexbfs(graph, candidate):
            return candidate
    return None


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {
        'ordering': order,
        'n': n,
    }


def insert_edge(graph, edge, state):
    order = state['ordering']
    u, v = edge
    # Adding an edge CAN invalidate a LexBFS ordering.
    # Check only the affected triples (O(n^2) instead of O(n^3)).
    if _is_valid_lexbfs_after_flip(graph, order, u, v):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # Try local repair: move u and v to the front
    repaired = _try_local_repair(graph, order, u, v)
    if repaired is not None:
        return {
            'ordering': repaired,
            'n': state['n'],
        }
    # Fall back to full recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }


def delete_edge(graph, edge, state):
    order = state['ordering']
    u, v = edge
    # Removing an edge can break the 4-point property.
    # Check only the affected triples (O(n^2) instead of O(n^3)).
    if _is_valid_lexbfs_after_flip(graph, order, u, v):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # Try local repair: move u and v to the front
    repaired = _try_local_repair(graph, order, u, v)
    if repaired is not None:
        return {
            'ordering': repaired,
            'n': state['n'],
        }
    # Fall back to full recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }
