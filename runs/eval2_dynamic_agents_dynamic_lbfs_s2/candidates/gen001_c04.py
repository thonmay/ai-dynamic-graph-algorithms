"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (try a few candidate reorderings and verify each with
the (LB) 4-point property); if none works, fall back to a full O(n^2)
LexBFS recompute.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _build_adj(graph):
    """Build adjacency bitmask list from 0/1 matrix."""
    n = len(graph)
    adj = [0] * n
    for v in range(n):
        row = graph[v]
        m = 0
        for u in range(n):
            if row[u]:
                m |= (1 << u)
        adj[v] = m
    return adj


def _lexbfs_full(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    adj = _build_adj(graph)

    # buckets: list of [label_mask, [v1, v2, ...]]
    # label_mask: bit i set iff the vertex at position i in the ordering
    #   so far is a neighbor of (all) vertices in this bucket.
    # Label comparison: earlier positions are more significant.
    #   m1 > m2 iff at the lowest set bit of (m1^m2), m1 has the bit set.
    buckets = [[0, list(range(n))]]
    ordering = []

    for pos in range(n):
        # Find bucket with lexicographically largest label.
        best = 0
        for i in range(1, len(buckets)):
            m1 = buckets[i][0]
            m0 = buckets[best][0]
            if m1 != m0:
                diff = m1 ^ m0
                low = diff & (-diff)
                if (m1 & low) != 0:
                    best = i
        mask, verts = buckets[best]
        v = verts.pop(0)
        if not verts:
            buckets.pop(best)
        ordering.append(v)
        # Refine all remaining buckets by adjacency to v.
        bit = 1 << pos
        new_buckets = []
        for bm, bverts in buckets:
            adj_to_v = []
            not_adj = []
            for w in bverts:
                if (adj[w] >> v) & 1:
                    adj_to_v.append(w)
                else:
                    not_adj.append(w)
            if adj_to_v:
                new_buckets.append([bm | bit, adj_to_v])
            if not_adj:
                new_buckets.append([bm, not_adj])
        buckets = new_buckets

    return ordering


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property. O(n^2) with bitsets."""
    n = len(ordering)
    if n <= 2:
        return True
    adj = _build_adj(graph)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    # before[p] = bitmask of vertices at positions 0..p-1
    before = [0] * (n + 1)
    for p in range(n):
        before[p + 1] = before[p] | (1 << ordering[p])

    for bi in range(n):
        b = ordering[bi]
        for ci in range(bi + 1, n):
            c = ordering[ci]
            # S = {a : pos[a] < bi, adj[a][c]=1, adj[a][b]=0}
            S = adj[c] & ~adj[b] & before[bi]
            if S == 0:
                continue
            # Find a* = vertex in S with smallest position
            a_star_pos = n + 1
            s = S
            while s:
                low = s & (-s)
                a = low.bit_length() - 1
                if pos[a] < a_star_pos:
                    a_star_pos = pos[a]
                s ^= low
            # Check: exists d with pos[d] < a_star_pos, adj[d][b]=1, adj[d][c]=0
            D = adj[b] & ~adj[c] & before[a_star_pos]
            if D == 0:
                return False
    return True


def _make_pos(ordering):
    n = len(ordering)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    return pos


def _try_repair(graph, edge, state):
    """Try local repair. Returns True if state is valid, False otherwise."""
    ordering = state['ordering']
    n = len(ordering)
    u, v = edge

    # First check if current ordering is still valid.
    if _is_valid_lexbfs(graph, ordering):
        return True

    # Try candidate reorderings: move u and/or v to front or back.
    rest = [x for x in ordering if x != u and x != v]
    candidates = [
        [x for x in ordering if x != u] + [u],
        [x for x in ordering if x != v] + [v],
        rest + [u, v],
        rest + [v, u],
        [u, v] + rest,
        [v, u] + rest,
    ]
    for cand in candidates:
        if _is_valid_lexbfs(graph, cand):
            state['ordering'] = cand
            state['pos'] = _make_pos(cand)
            return True
    return False


def _full_recompute(graph, state):
    ordering = _lexbfs_full(graph)
    state['ordering'] = ordering
    state['pos'] = _make_pos(ordering)
    return state


def init(graph):
    n = len(graph)
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering, 'pos': _make_pos(ordering)}


def insert_edge(graph, edge, state):
    if not _try_repair(graph, edge, state):
        _full_recompute(graph, state)
    return state


def delete_edge(graph, edge, state):
    if not _try_repair(graph, edge, state):
        _full_recompute(graph, state)
    return state
