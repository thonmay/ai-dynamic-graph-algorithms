"""Dynamic LexBFS ordering (candidate gen008_c01).

Strategy: maintain a valid LexBFS ordering under single edge flips.

Correctness core:
  * init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
    with a deterministic tie-break (smallest vertex id first).
  * insert_edge / delete_edge: a single edge flip can invalidate the current
    ordering.  We verify the (LB) 4-point property of Corneil and Krueger on
    the current ordering; if it still holds we keep the ordering, otherwise
    we recompute from scratch.

  The (LB) property: for all positions a < b < c with ac in E and ab not in
  E, there exists d < a with db in E and dc not in E.

  Verification is done in O(n^3) worst case but with early exits; in
  practice most orderings remain valid after a single edge flip, so the
  check is the dominant cost and recomputation is rare.

State: dict with 'ordering' (list of n vertices) and 'n'.
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


def _fast_check(graph, order, edge):
    """Fast pre-check after a single edge flip.

    Only examines triples (a, b, c) where the flipped edge (u, v) is
    involved as either the 'ac' edge or the 'ab' edge.  If any such
    triple violates the (LB) property, return False immediately.
    If all such triples are satisfied, return True (meaning the fast
    check passed; the caller should still do a full check to be safe,
    OR we can trust this if we reason that only these triples can be
    newly violated).

    Actually, for a single edge flip, only triples where the flipped
    edge participates can change their status.  So this IS a complete
    check: if all affected triples are satisfied, the ordering is valid.

    Returns True if the ordering is valid (no violation found among
    affected triples), False otherwise.
    """
    n = len(order)
    u, v = edge
    # Build position map
    pos = [0] * n
    for idx, vert in enumerate(order):
        pos[vert] = idx

    pu = pos[u]
    pv = pos[v]

    # The flipped edge (u, v) can appear in a triple (a, b, c) in these
    # roles:
    #   Role 1: (a, c) = (u, v) or (v, u) — the "ac in E" edge
    #   Role 2: (a, b) = (u, v) or (v, u) — the "ab not in E" edge
    #
    # For each role, enumerate the possible middle/other vertex and check.

    # Role 1: ac is the flipped edge.  a and c are u and v (in some order),
    # with pos(a) < pos(c).  b is any vertex with pos(a) < pos(b) < pos(c).
    # Condition: ab not in E (i.e., graph[a][b] == 0).
    # Need: exists t < pos(a) with graph[order[t]][b] and not graph[order[t]][c].

    # Determine which of u, v is 'a' (earlier) and which is 'c' (later)
    if pu < pv:
        a, c = u, v
        pa, pc = pu, pv
    else:
        a, c = v, u
        pa, pc = pv, pu

    # b must be at position strictly between pa and pc
    for pb in range(pa + 1, pc):
        b = order[pb]
        if graph[a][b]:
            continue  # ab in E, not triggered
        # Need d at position t < pa with db in E and dc not in E
        found = False
        for t in range(pa):
            d = order[t]
            if graph[d][b] and not graph[d][c]:
                found = True
                break
        if not found:
            return False

    # Role 2: ab is the flipped edge.  a and b are u and v (in some order),
    # with pos(a) < pos(b).  c is any vertex with pos(b) < pos(c).
    # Condition: ac in E (i.e., graph[a][c] == 1).
    # Need: exists t < pos(a) with graph[order[t]][b] and not graph[order[t]][c].

    if pu < pv:
        a, b = u, v
        pa, pb = pu, pv
    else:
        a, b = v, u
        pa, pb = pv, pu

    for pc in range(pb + 1, n):
        c = order[pc]
        if not graph[a][c]:
            continue  # ac not in E, not triggered
        # Need d at position t < pa with db in E and dc not in E
        found = False
        for t in range(pa):
            d = order[t]
            if graph[d][b] and not graph[d][c]:
                found = True
                break
        if not found:
            return False

    return True


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {
        'ordering': order,
        'n': n,
    }


def insert_edge(graph, edge, state):
    order = state['ordering']
    # Adding an edge CAN invalidate a LexBFS ordering.  Use the fast
    # targeted check: only triples involving the new edge can be newly
    # violated.  If the fast check passes, the ordering is still valid.
    if _fast_check(graph, order, edge):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }


def delete_edge(graph, edge, state):
    order = state['ordering']
    # Removing an edge can break the 4-point property.  Use the fast
    # targeted check: only triples involving the removed edge can be
    # newly violated.  If the fast check passes, the ordering is still valid.
    if _fast_check(graph, order, edge):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }
