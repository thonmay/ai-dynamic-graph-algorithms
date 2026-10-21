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
- The position map and the position-neighbor bitmasks (bits) are cached in
  the state and updated in O(n) per edge flip, so the incremental check
  itself is O(n^2 / word) with no per-update O(n^2) rebuild.
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


def _build_pos_bits(ordering, adj):
    """pos[v] = position of v; bits[v] = bitmask of positions of v's
    neighbors (bit i set iff ordering[i] is adjacent to v)."""
    n = len(ordering)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    bits = [0] * n
    for i, w in enumerate(ordering):
        bit = 1 << i
        row = adj[w]
        for v in range(n):
            if (row >> v) & 1:
                bits[v] |= bit
    return pos, bits


def _check_lb_full(ordering, adj):
    """Check the (LB) 4-point property. Returns True if ordering is valid LexBFS."""
    n = len(ordering)
    if n <= 2:
        return True

    pos, bits = _build_pos_bits(ordering, adj)
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


def _check_lb_incremental(ordering, adj, pos, bits, edge):
    """Check (LB) only for triples whose status can change after flipping
    edge (u, v).  pos and bits must already reflect the new graph.
    Returns True if the ordering is still valid."""
    n = len(ordering)
    if n <= 2:
        return True

    u, v = edge
    mask_all = (1 << n) - 1
    pu, pv = pos[u], pos[v]

    # Affected triples (a, b, c) are those where the flipped edge touches
    # a, b, or c.  (The witness d is distinct from a, b, c, so the witness
    # condition db/dc can only change if b or c is an endpoint.)
    #
    # Case 1: a or b is an endpoint -> check the whole pair (a, b).
    #
    # p as a (i = p): for each non-neighbor b at j > p, the failing c's are
    #   C_j = { k > j : ac in E and (bits[b] & ~bits[c] & dmask) = 0 }
    # and the pair fails iff C_j is non-empty.  C_j is one big-int op per j.
    if pu < pv:
        p_lo, p_hi = pu, pv
    else:
        p_lo, p_hi = pv, pu
    for p in (p_lo, p_hi):
        a = ordering[p]
        ba = bits[a]
        dmask = (1 << p) - 1
        cand_b = (~ba) & mask_all & ~((1 << (p + 1)) - 1)
        while cand_b:
            lb = cand_b & (-cand_b)
            j = lb.bit_length() - 1
            b = ordering[j]
            cand_b ^= lb
            # c positions: k > j with ac in E.
            cand_c = ba & mask_all & ~((1 << (j + 1)) - 1)
            if not cand_c:
                continue
            # c positions with a witness d < p for b.
            good = 0
            while cand_c:
                lc = cand_c & (-cand_c)
                c = ordering[lc.bit_length() - 1]
                cand_c ^= lc
                if bits[b] & (~bits[c]) & dmask:
                    good |= lc
            if cand_c & ~good:
                return False
        # p as b (j = p): for each a at i < p with ab not in E, the failing
        # c's are C_i = { k > p : ac in E and (bits[b] & ~bits[c] & dmask) = 0 }.
        b = ordering[p]
        bb = bits[b]
        cand_a = (~bb) & ((1 << p) - 1)
        while cand_a:
            la = cand_a & (-cand_a)
            i = la.bit_length() - 1
            a = ordering[i]
            cand_a ^= la
            dmask = (1 << i) - 1
            cand_c = bits[a] & mask_all & ~((1 << (p + 1)) - 1)
            if not cand_c:
                continue
            good = 0
            while cand_c:
                lc = cand_c & (-cand_c)
                c = ordering[lc.bit_length() - 1]
                cand_c ^= lc
                if bb & (~bits[c]) & dmask:
                    good |= lc
            if cand_c & ~good:
                return False

    # Case 2: c is an endpoint p, but a and b are not.  Then only the
    # specific triple (a, b, p) is affected (p enters/leaves the set of
    # c's with ac in E, and the witness condition for c=p changes).
    #
    # For fixed i (a at position i), the failing b's are exactly
    #   B_i = { j in (i, p) : ab not in E and (bits[b] & ~bits[c] & dmask) = 0 }
    # and the triple fails iff B_i intersects N_i = { j in (i, p) : ac in E }.
    # B_i is computed with one big-int op per i.
    for p in (pu, pv):
        c = ordering[p]
        bc = bits[c]
        for i in range(p):
            a = ordering[i]
            ba = bits[a]
            dmask = (1 << i) - 1
            # b positions in (i, p) with ab not in E.
            cand_b = (~ba) & mask_all & ~((1 << (i + 1)) - 1) & ~((1 << p) - 1)
            if not cand_b:
                continue
            # b positions in (i, p) with a witness d < i for c.
            good = 0
            while cand_b:
                lb = cand_b & (-cand_b)
                b = ordering[lb.bit_length() - 1]
                cand_b ^= lb
                if bits[b] & (~bc) & dmask:
                    good |= lb
            # Failing b's: no witness.  If any of them is adjacent to a,
            # the triple (a, b, c) violates (LB).
            if (cand_b & ~good) & ba:
                return False
    return True


def _update_pos_bits(pos, bits, u, v, add):
    """Update pos and bits after flipping edge (u, v) in place.
    add=True for insertion, False for deletion."""
    pu, pv = pos[u], pos[v]
    bu, bv = 1 << pu, 1 << pv
    if add:
        bits[u] |= bv
        bits[v] |= bu
    else:
        bits[u] &= ~bv
        bits[v] &= ~bu


def init(graph):
    ordering = _lexbfs(graph)
    adj = _adj_masks(graph)
    pos, bits = _build_pos_bits(ordering, adj)
    return {'ordering': ordering, 'adj': adj, 'pos': pos, 'bits': bits}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']
    pos = state['pos']
    bits = state['bits']
    adj[u] |= (1 << v)
    adj[v] |= (1 << u)
    _update_pos_bits(pos, bits, u, v, True)
    if not _check_lb_incremental(ordering, adj, pos, bits, edge):
        state['ordering'] = _lexbfs(graph)
        state['adj'] = _adj_masks(graph)
        state['pos'], state['bits'] = _build_pos_bits(state['ordering'], state['adj'])
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']
    pos = state['pos']
    bits = state['bits']
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    _update_pos_bits(pos, bits, u, v, False)
    if not _check_lb_incremental(ordering, adj, pos, bits, edge):
        state['ordering'] = _lexbfs(graph)
        state['adj'] = _adj_masks(graph)
        state['pos'], state['bits'] = _build_pos_bits(state['ordering'], state['adj'])
    return state
