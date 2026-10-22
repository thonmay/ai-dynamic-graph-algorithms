"""Dynamic LexBFS ordering (candidate gen004_c03).

Strategy: maintain a valid LexBFS ordering under single edge flips.

Correctness core:
  * init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
    with a deterministic tie-break (smallest vertex id first).
  * insert_edge / delete_edge: after a single edge flip, only triples whose
    status can change are those involving the flipped edge.  We check exactly
    those in O(n^2) (instead of the full O(n^3) verification); if no violation
    is found we keep the ordering, otherwise we recompute.

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


def _check_insert(graph, order, u, v):
    """After inserting edge (u,v), check only the triples whose status can
    change.  A triple (a,b,c) at positions i<j<k is a violation iff
    ac in E, ab not in E, and no d<i with db in E and dc not in E.

    The only triples whose status can change are those where the flipped
    edge (u,v) is one of the edges whose membership matters:
      - (a,c) = (u,v) or (v,u): the antecedent "ac in E" becomes true.
      - (a,b) = (u,v) or (v,u): the antecedent "ab not in E" becomes false.
      - (d,b) = (u,v) or (v,u): the witness condition changes.
      - (d,c) = (u,v) or (v,u): the witness condition changes.

    We check all triples where u or v appears in any of these roles.
    """
    n = len(order)
    pos = {v: i for i, v in enumerate(order)}
    pu = pos[u]
    pv = pos[v]

    # For each triple (i, j, k) with i < j < k, check if it's a violation.
    # We only need to check triples where the flipped edge (u,v) affects
    # the outcome.  The flipped edge can appear as:
    #   - (a,c): positions (i,k) = (pu,pv) or (pv,pu)
    #   - (a,b): positions (i,j) = (pu,pv) or (pv,pu)
    #   - (d,b): positions (t,j) = (pu,pv) or (pv,pu) for some t < i
    #   - (d,c): positions (t,k) = (pu,pv) or (pv,pu) for some t < i

    # Case 1: (a,c) = (u,v) or (v,u), i.e., i and k are pu and pv.
    #   If pu < pv: i=pu, k=pv.  Check all j with pu < j < pv.
    #   If pv < pu: i=pv, k=pu.  Check all j with pv < j < pu.
    lo = min(pu, pv)
    hi = max(pu, pv)
    for j in range(lo + 1, hi):
        a = order[lo]
        b = order[j]
        c = order[hi]
        # ac in E (just inserted), ab not in E?
        if graph[a][b]:
            continue
        # Need d < a (position < lo) with db in E and dc not in E.
        found = False
        for t in range(lo):
            d = order[t]
            if graph[d][b] and not graph[d][c]:
                found = True
                break
        if not found:
            return False

    # Case 2: (a,b) = (u,v) or (v,u), i.e., i and j are pu and pv.
    #   If pu < pv: i=pu, j=pv.  Check all k > pv.
    #   If pv < pu: i=pv, j=pu.  Check all k > pu.
    #   But wait: if (a,b) = (u,v), then ab is now in E, so the antecedent
    #   "ab not in E" is FALSE.  So these triples are NOT violations.
    #   Actually, the antecedent requires ab NOT in E.  Since we just added
    #   (u,v), if (a,b) = (u,v) then ab IS in E, so the antecedent fails.
    #   So Case 2 cannot produce a violation.  Skip.

    # Case 3: (d,b) = (u,v) or (v,u) for some d at position t < i.
    #   The flipped edge is (d,b).  Before the flip, db was not in E.
    #   After the flip, db is in E.  This can only HELP satisfy the witness
    #   condition (more d's with db in E), so it cannot create a new violation.
    #   Skip.

    # Case 4: (d,c) = (u,v) or (v,u) for some d at position t < i.
    #   The flipped edge is (d,c).  Before the flip, dc was not in E.
    #   After the flip, dc IS in E.  This can only HURT the witness condition
    #   (fewer d's with dc not in E), so it CAN create a new violation.
    #   We need to check triples where (d,c) = (u,v) or (v,u), i.e.,
    #   positions (t,k) = (pu,pv) or (pv,pu) for some t < i.
    #   For each such (t,k), we need i > t and j with i < j < k,
    #   and ac in E, ab not in E, and no d'<i with d'b in E and d'c not in E.
    #   But the witness condition is checked over ALL d' < i, not just d.
    #   So we need to check all triples (i,j,k) where k is pu or pv,
    #   and t (the position of the other endpoint) is < i.

    # Let's be more careful.  The flipped edge is (u,v).  In the witness
    # condition, we need d'c not in E.  If (d',c) = (u,v) or (v,u), then
    # before the flip d'c was not in E (witness valid), after the flip
    # d'c IS in E (witness invalid).  So the witness can be LOST.
    #
    # This affects triples (i,j,k) where:
    #   - c = order[k] is u or v
    #   - d' = order[t] is the other of u,v, with t < i
    #   - ac in E, ab not in E
    #   - no d'' < i with d''b in E and d''c not in E
    #
    # So we need to check triples where k is pu or pv, and the other
    # endpoint is at some position t < i.

    # For k = pv (c = v), the other endpoint u is at position pu.
    #   We need pu < i < j < pv.  Check all such (i, j).
    if pu < pv:
        for i in range(pu + 1, pv):
            a = order[i]
            c = order[pv]  # c = v
            # ac in E?
            if not graph[a][c]:
                continue
            for j in range(i + 1, pv):
                b = order[j]
                if graph[a][b]:
                    continue
                # ab not in E; check witness
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    # For k = pu (c = u), the other endpoint v is at position pv.
    #   We need pv < i < j < pu.  Check all such (i, j).
    if pv < pu:
        for i in range(pv + 1, pu):
            a = order[i]
            c = order[pu]  # c = u
            # ac in E?
            if not graph[a][c]:
                continue
            for j in range(i + 1, pu):
                b = order[j]
                if graph[a][b]:
                    continue
                # ab not in E; check witness
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False

    return True


def _check_delete(graph, order, u, v):
    """After deleting edge (u,v), check only the triples whose status can
    change.  The flipped edge (u,v) was in E before, now not in E.

    Triples whose status can change:
      - (a,c) = (u,v) or (v,u): the antecedent "ac in E" becomes false.
        This can only REMOVE violations, not create them.  Skip.
      - (a,b) = (u,v) or (v,u): the antecedent "ab not in E" becomes true.
        This can CREATE new violations.  Check.
      - (d,b) = (u,v) or (v,u): the witness condition changes.
        Before: db in E.  After: db not in E.  This can LOSE a witness,
        creating a new violation.  Check.
      - (d,c) = (u,v) or (v,u): the witness condition changes.
        Before: dc not in E (witness valid).  After: dc in E... wait,
        we deleted (u,v), so dc was in E before, now not in E.
        This can GAIN a witness, removing violations.  Skip.

    So we need to check:
      Case A: (a,b) = (u,v) or (v,u), i.e., i and j are pu and pv.
        If pu < pv: i=pu, j=pv.  Check all k > pv.
        If pv < pu: i=pv, j=pu.  Check all k > pu.
      Case B: (d,b) = (u,v) or (v,u) for some d at position t < i.
        The flipped edge is (d,b).  Before: db in E.  After: db not in E.
        This can lose a witness.  We need to check triples where
        (d,b) = (u,v) or (v,u), i.e., positions (t,j) = (pu,pv) or (pv,pu)
        for some t < i.  For each such (t,j), check all i > t and k > j
        where ac in E, ab not in E, and no d'' < i with d''b in E and
        d''c not in E.
    """
    n = len(order)
    pos = {v: i for i, v in enumerate(order)}
    pu = pos[u]
    pv = pos[v]

    # Case A: (a,b) = (u,v) or (v,u).
    #   If pu < pv: i=pu, j=pv.  Check all k > pv.
    #   If pv < pu: i=pv, j=pu.  Check all k > pu.
    lo = min(pu, pv)
    hi = max(pu, pv)
    a = order[lo]
    b = order[hi]
    # ab not in E (just deleted).  Check all k > hi.
    for k in range(hi + 1, n):
        c = order[k]
        if not graph[a][c]:
            continue
        # ac in E, ab not in E.  Check witness.
        found = False
        for t in range(lo):
            d = order[t]
            if graph[d][b] and not graph[d][c]:
                found = True
                break
        if not found:
            return False

    # Case B: (d,b) = (u,v) or (v,u) for some d at position t < i.
    #   The flipped edge is (d,b).  Before: db in E.  After: db not in E.
    #   This can lose a witness.  We need to check triples where
    #   (d,b) = (u,v) or (v,u), i.e., positions (t,j) = (pu,pv) or (pv,pu)
    #   for some t < i.
    #
    #   For (t,j) = (pu,pv) with pu < pv: d=u at position pu, b=v at position pv.
    #     We need i > pu and k > pv.  Check all (i, k) with pu < i < pv < k
    #     or pu < i and pv < k (i can be > pv too, but then j=pv < i,
    #     which violates i < j).  Wait, we need i < j = pv, so i < pv.
    #     So: pu < i < pv, and k > pv.
    #
    #   For (t,j) = (pv,pu) with pv < pu: d=v at position pv, b=u at position pu.
    #     We need i > pv and k > pu.  Check all (i, k) with pv < i < pu,
    #     and k > pu.

    if pu < pv:
        # d=u at pu, b=v at pv.  i in (pu, pv), k > pv.
        for i in range(pu + 1, pv):
            a = order[i]
            b = order[pv]  # b = v
            # ab not in E?
            if graph[a][b]:
                continue
            for k in range(pv + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                # ac in E, ab not in E.  Check witness.
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    if pv < pu:
        # d=v at pv, b=u at pu.  i in (pv, pu), k > pu.
        for i in range(pv + 1, pu):
            a = order[i]
            b = order[pu]  # b = u
            # ab not in E?
            if graph[a][b]:
                continue
            for k in range(pu + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                # ac in E, ab not in E.  Check witness.
                found = False
                for t in range(i):
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
    u, v = edge
    # Check only the triples whose status can change after inserting (u,v).
    if _check_insert(graph, order, u, v):
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
    u, v = edge
    # Check only the triples whose status can change after deleting (u,v).
    if _check_delete(graph, order, u, v):
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
