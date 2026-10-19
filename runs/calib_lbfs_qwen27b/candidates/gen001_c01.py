"""Dynamic LexBFS ordering (open problem tier).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge: the old ordering stays a valid LexBFS unless the new edge
  (u,v) is a "violation" (u before v, u has a non-neighbor before v, and v
  has a neighbor before u).  If violated, move u to the front of the
  ordering; the (LB) 4-point property is then restored.
- delete_edge: the old ordering stays a valid LexBFS unless the deleted
  edge (u,v) was "essential": u before v, u has a non-neighbor before v,
  and v's only neighbor before u is u itself.  If essential, recompute
  from scratch (rare; correctness first).

Validity is certified by the (LB) 4-point property of Corneil & Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs(adj):
    """Static partition-refinement LexBFS.  Returns (ordering, pos)."""
    n = len(adj)
    # buckets: list of lists of vertices, in current order
    buckets = [[v] for v in range(n)]
    # for each vertex, the index of the bucket it currently sits in
    bidx = list(range(n))
    # for each vertex, the position (offset) inside its bucket
    offset = [0] * n
    # pos[v] = current global position of v
    pos = list(range(n))
    # neighbors[v] = set of neighbors of v (for O(1) membership)
    nbrs = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(n):
            if row[v]:
                nbrs[u].add(v)

    for s in range(n):
        # split every bucket by adjacency to s
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            b0 = []
            b1 = []
            for v in b:
                if s in nbrs[v]:
                    b1.append(v)
                else:
                    b0.append(v)
            if b1:
                new_buckets.append(b1)
            if b0:
                new_buckets.append(b0)
        buckets = new_buckets
        # recompute bidx / offset / pos
        p = 0
        for bi, b in enumerate(buckets):
            for off, v in enumerate(b):
                bidx[v] = bi
                offset[v] = off
                pos[v] = p
                p += 1
        # pick next vertex: first bucket with >1 vertices, else first bucket
        chosen = None
        for bi, b in enumerate(buckets):
            if len(b) > 1:
                chosen = b[0]
                break
        if chosen is None:
            for b in buckets:
                if b:
                    chosen = b[0]
                    break
        # remove chosen from its bucket
        bi = bidx[chosen]
        b = buckets[bi]
        b.remove(chosen)
        if not b:
            del buckets[bi]
            # fix bidx for remaining vertices in later buckets
            p = 0
            for bi2, b2 in enumerate(buckets):
                for off, v in enumerate(b2):
                    bidx[v] = bi2
                    offset[v] = off
                    pos[v] = p
                    p += 1
        else:
            # fix offset/pos for vertices after chosen in the same bucket
            off = offset[chosen]
            for v in b[off:]:
                offset[v] -= 1
                pos[v] -= 1
            # fix pos for all vertices in later buckets
            p = pos[chosen] + 1
            for bi2 in range(bi + 1, len(buckets)):
                for v in buckets[bi2]:
                    pos[v] = p
                    p += 1
    ordering = [0] * n
    for v in range(n):
        ordering[pos[v]] = v
    return ordering, pos


def _is_violation(adj, pos, u, v):
    """Check whether edge (u,v) violates the (LB) property of the
    current ordering (u before v).  Returns True if violated."""
    pu, pv = pos[u], pos[v]
    if pu > pv:
        u, v, pu, pv = v, u, pv, pu
    # u before v, edge uv exists
    # violation iff: exists b with pu < pos[b] < pv, not adj[u][b],
    #                and exists c with pos[c] < pu, adj[v][c]
    has_nonnbr = False
    for b in range(pu + 1, pv):
        if not adj[u][b]:
            has_nonnbr = True
            break
    if not has_nonnbr:
        return False
    for c in range(pu):
        if adj[v][c]:
            return True
    return False


def _is_essential(adj, pos, u, v):
    """Check whether deleting edge (u,v) (u before v) breaks the (LB)
    property: u has a non-neighbor before v, and v's only neighbor
    before u is u itself."""
    pu, pv = pos[u], pos[v]
    if pu > pv:
        u, v, pu, pv = v, u, pv, pu
    has_nonnbr = False
    for b in range(pu + 1, pv):
        if not adj[u][b]:
            has_nonnbr = True
            break
    if not has_nonnbr:
        return False
    for c in range(pu):
        if adj[v][c]:
            return False
    return True


def init(graph):
    ordering, pos = _lexbfs(graph)
    return {'ordering': ordering, 'pos': pos}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    pos = state['pos']
    if _is_violation(graph, pos, u, v):
        # move u (the earlier endpoint) to the front
        pu, pv = pos[u], pos[v]
        if pu > pv:
            u, v = v, u
        # remove u from its position
        ordering.pop(pu)
        ordering.insert(0, u)
        # rebuild pos
        pos = [0] * len(ordering)
        for i, x in enumerate(ordering):
            pos[x] = i
    return {'ordering': ordering, 'pos': pos}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    pos = state['pos']
    if _is_essential(graph, pos, u, v):
        ordering, pos = _lexbfs(graph)
    return {'ordering': ordering, 'pos': pos}
