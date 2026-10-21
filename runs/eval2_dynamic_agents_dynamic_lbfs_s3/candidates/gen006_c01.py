"""Dynamic LexBFS ordering (undirected).

Strategy: maintain a valid LexBFS ordering.  On each update, verify the
(LB) 4-point property on the new graph; if it fails, recompute from
scratch with the standard partition-refinement LexBFS (O(n+m)).

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.

Optimizations over the naive check:
- Adjacency is cached in the state as Python int bitmasks (one per vertex),
  so the check runs in O(n^3 / word) instead of O(n^4).
- The check is incremental: only triples involving the updated edge can
  change status, so we only re-examine those.
- The recompute uses the true O(n+m) partition-refinement LexBFS
  (Habib-McConnell-Paul-Viennot) instead of the O(n^2) label-scan.
"""


def _adj_masks(graph):
    """Build adjacency as a list of int bitmasks (bit j set iff i-j edge)."""
    n = len(graph)
    masks = [0] * n
    for i in range(n):
        row = graph[i]
        m = 0
        for j in range(n):
            if row[j]:
                m |= 1 << j
        masks[i] = m
    return masks


def _lexbfs(graph):
    """Partition-refinement LexBFS (HMPV). Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    adj = _adj_masks(graph)

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
                if (adj[v] >> x) & 1:
                    Tn.add(x)
                else:
                    Ty.add(x)
            if Tn:
                newP.append(Tn)
            if Ty:
                newP.append(Ty)
        P = newP

    return ordered


def _check_lb_full(ordering, adj):
    """Check the (LB) 4-point property. Returns True if ordering is valid LexBFS."""
    n = len(ordering)
    if n <= 2:
        return True

    # pos[v] = position of vertex v in the ordering.
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    # bits[v] = bitmask of positions of v's neighbors (bit i set iff
    # ordering[i] is adjacent to v).
    bits = [0] * n
    for i, w in enumerate(ordering):
        bit = 1 << i
        row = adj[w]
        for v in range(n):
            if (row >> v) & 1:
                bits[v] |= bit

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


def _check_lb_incremental(ordering, adj, edge):
    """Check (LB) only for triples whose status can change after flipping
    edge (u, v).  Returns True if the ordering is still valid."""
    n = len(ordering)
    if n <= 2:
        return True

    u, v = edge
    pos = [0] * n
    for i, w in enumerate(ordering):
        pos[w] = i
    bits = [0] * n
    for i, w in enumerate(ordering):
        bit = 1 << i
        row = adj[w]
        for x in range(n):
            if (row >> x) & 1:
                bits[x] |= bit

    mask_all = (1 << n) - 1
    pu, pv = pos[u], pos[v]

    def check_pair(i, j):
        # i = position of a, j = position of b, i < j, ab not in E.
        a = ordering[i]
        b = ordering[j]
        if (adj[a] >> b) & 1:
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
            if (adj[a] >> c) & 1:
                dmask = (1 << i) - 1
                for j in range(i + 1, p):
                    b = ordering[j]
                    if (adj[a] >> b) & 1:
                        continue  # ab in E: no constraint.
                    if not (bits[b] & (~bits[c]) & dmask):
                        return False
    return True


def init(graph):
    ordering = _lexbfs(graph)
    adj = _adj_masks(graph)
    return {'ordering': ordering, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']
    adj[u] |= (1 << v)
    adj[v] |= (1 << u)
    if not _check_lb_incremental(ordering, adj, edge):
        state['ordering'] = _lexbfs(graph)
        state['adj'] = _adj_masks(graph)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    if not _check_lb_incremental(ordering, adj, edge):
        state['ordering'] = _lexbfs(graph)
        state['adj'] = _adj_masks(graph)
    return state
