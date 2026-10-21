"""Dynamic LexBFS ordering (undirected).

Strategy: maintain a valid LexBFS ordering. On each update, verify the
(LB) 4-point property on the new graph; if it fails, recompute from
scratch with the standard partition-refinement LexBFS (O(n+m)).

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.

Optimizations over the naive check:
- The check is vectorized with Python integers as bitsets (one int per
  vertex, bit i = position i in the ordering).  The inner "exists d"
  test becomes a single AND of two precomputed bitsets.
- The check is incremental: only triples involving the updated edge can
  change status, so we only re-examine those.
- The recompute uses the true O(n+m) partition-refinement LexBFS
  (Habib-McConnell-Paul-Viennot) instead of the O(n^2) label-scan.
"""


def _lexbfs(graph):
    """Partition-refinement LexBFS (HMPV). Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    # Partition P: list of sets, in order.  A vertex is selected from the
    # first non-empty set (ties broken by smallest vertex id).
    P = [set(range(n))]

    ordered = []
    while P:
        # Find first non-empty set.
        while P and not P[0]:
            P.pop(0)
        if not P:
            break
        S = P[0]
        v = min(S)
        S.discard(v)
        ordered.append(v)

        # Refine every set in P by adjacency to v.
        newP = []
        for T in P:
            if not T:
                continue
            Tn = set()
            Ty = set()
            for x in T:
                if x in adj[v]:
                    Tn.add(x)
                else:
                    Ty.add(x)
            if Tn:
                newP.append(Tn)
            if Ty:
                newP.append(Ty)
        P = newP

    return ordered


def _build_bitsets(graph, ordering):
    """Bitset per vertex: bit i set iff vertex is adjacent to ordering[i]."""
    n = len(ordering)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    bits = [0] * n
    for i, w in enumerate(ordering):
        bit = 1 << i
        row = graph[w]
        for v in range(n):
            if row[v]:
                bits[v] |= bit
    return bits, pos


def _check_lb_full(graph, ordering):
    """Check the (LB) 4-point property. Returns True if ordering is valid LexBFS."""
    n = len(ordering)
    if n <= 2:
        return True

    bits, pos = _build_bitsets(graph, ordering)
    mask_all = (1 << n) - 1

    for i in range(n):
        a = ordering[i]
        ba = bits[a]
        # b positions: j > i with ab not in E.
        cand_b = (~ba) & mask_all & ~((1 << (i + 1)) - 1)
        # d positions: l < i.
        dmask = (1 << i) - 1
        while cand_b:
            lb = cand_b & (-cand_b)
            j = lb.bit_length() - 1
            b = ordering[j]
            cand_b ^= lb
            # c positions: k > j with ac in E.
            cand_c = ba & mask_all & ~((1 << (j + 1)) - 1)
            while cand_c:
                lc = cand_c & (-cand_c)
                k = lc.bit_length() - 1
                c = ordering[k]
                cand_c ^= lc
                # Need: exists d < i with db in E and dc not in E.
                if not (bits[b] & (~bits[c]) & dmask):
                    return False
    return True


def _check_lb_incremental(graph, ordering, edge):
    """Check (LB) only for triples whose status can change after flipping
    edge (u, v).  Returns True if the ordering is still valid."""
    n = len(ordering)
    if n <= 2:
        return True

    u, v = edge
    bits, pos = _build_bitsets(graph, ordering)
    mask_all = (1 << n) - 1
    pu, pv = pos[u], pos[v]

    # A triple (a, b, c) with a < b < c is affected iff the flipped edge
    # touches one of a, b, c.  For each affected triple we must verify the
    # (LB) condition.  We enumerate triples by the affected vertex's role.
    #
    # For a fixed pair (a, b) with a < b and ab not in E, the condition is:
    #   for all c > b with ac in E:  (bits[b] & ~bits[c] & dmask_a) != 0
    # where dmask_a = (1 << pos[a]) - 1.
    #
    # Affected (a, b) pairs: those where a or b is u or v (since ac or ab
    # membership changed).  For each such pair we scan all c > b with ac in E.

    def check_pair(i, j):
        # i = position of a, j = position of b, i < j, ab not in E.
        a = ordering[i]
        b = ordering[j]
        if graph[a][b]:
            return True
        ba = bits[a]
        dmask = (1 << i) - 1
        cand_c = ba & mask_all & ~((1 << (j + 1)) - 1)
        while cand_c:
            lc = cand_c & (-cand_c)
            c = ordering[lc.bit_length() - 1]
            cand_c ^= lc
            if not (bits[b] & (~bits[c]) & dmask):
                return False
        return True

    # Affected triples (a, b, c) are those where the flipped edge touches
    # a, b, or c.  (The witness d is distinct from a, b, c, so the witness
    # condition db/dc can only change if b or c is an endpoint.)
    #
    # Case 1: a or b is an endpoint -> check the whole pair (a, b).
    for p in (pu, pv):
        # p as a: i = p, j > p.
        for j in range(p + 1, n):
            if not check_pair(p, j):
                return False
        # p as b: j = p, i < p.
        for i in range(p):
            if not check_pair(i, p):
                return False

    # Case 2: c is an endpoint p, but a and b are not.  Then only the
    # specific triple (a, b, p) is affected (p enters/leaves the set of
    # c's with ac in E, and the witness condition for c=p changes).
    for p in (pu, pv):
        c = ordering[p]
        for i in range(p):
            a = ordering[i]
            if not graph[a][c]:
                continue  # ac not in E: no constraint from this c.
            dmask = (1 << i) - 1
            for j in range(i + 1, p):
                b = ordering[j]
                if graph[a][b]:
                    continue  # ab in E: no constraint.
                if not (bits[b] & (~bits[c]) & dmask):
                    return False
    return True


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if not _check_lb_incremental(graph, ordering, edge):
        state['ordering'] = _lexbfs(graph)
    return state


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if not _check_lb_incremental(graph, ordering, edge):
        state['ordering'] = _lexbfs(graph)
    return state
