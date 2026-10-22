"""Dynamic LexBFS ordering (candidate gen004_c03).

Derived from gen001_c03.  Same strategy, but the (LB) 4-point check is
replaced by a much cheaper *local* check that exploits the fact that only
one edge changed since the ordering was last verified.

Key observation
---------------
Let sigma be a valid LexBFS ordering of G, and let G' = G + e (or G - e)
for a single edge e = (u, v).  The (LB) 4-point property of sigma in G'
can only be violated by a witness triple (a, b, c) that involves u or v:
any triple that does not involve u or v had its witness d in G, and d's
adjacency to b and c is unchanged, so the triple is still witnessed.

So after an update we only need to check triples (a, b, c) with
pos[a] < pos[b] < pos[c], a~c, a not~ b, where {a, b, c} contains u or v.
That is O(n^2) in the worst case (one of the three roles is fixed to u or
v), versus O(n^3) for the full check.

If the local check passes, the ordering is still a valid LexBFS and we
keep it (no recompute).  Otherwise we recompute from scratch.

Work per update: O(n^2) local check, O(n^2) recompute only when needed.
"""


def _lexbfs(graph):
    """Static partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    buckets = [list(range(n))]
    order = []
    remaining = n

    while remaining > 0:
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = buckets[bi][0]
        buckets[bi].pop(0)
        order.append(v)
        remaining -= 1

        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = [x for x in b if graph[v][x]]
            nnb = [x for x in b if not graph[v][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets

    return order


def _local_check(graph, ordering, u, v):
    """Check the (LB) 4-point property for triples involving u or v.

    Assumes the ordering was valid before the single edge (u, v) was
    flipped.  Returns True iff the ordering is still a valid LexBFS
    ordering of the current graph.

    A triple (a, b, c) with pa < pb < pc, a~c, a not~ b, that does NOT
    involve u or v was witnessed in the previous graph, and the witness
    d's adjacency to b and c is unchanged, so it is still witnessed.
    Hence only triples containing u or v need checking.
    """
    n = len(ordering)
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i

    # For each vertex x, precompute:
    #   D[x] = list of (pd, d) with pos[d] < pos[x] and d ~ x
    # This is O(n^2) total.
    D = [None] * n
    for x in range(n):
        px = pos[x]
        gx = graph[x]
        D[x] = [(pd, ordering[pd]) for pd in range(px) if gx[ordering[pd]]]

    def triple_ok(a, b, c):
        """Witness check for one triple (a, b, c) with pa < pb < pc,
        a~c, a not~ b.  Returns True if witnessed."""
        pa = pos[a]
        for pd, d in D[b]:
            if pd < pa and not graph[d][c]:
                return True
        return False

    # Case 1: b is u or v.
    for b in (u, v):
        pb = pos[b]
        Db = D[b]
        for pa in range(pb):
            a = ordering[pa]
            if graph[a][b]:
                continue  # a~b, not a violating triple
            ga = graph[a]
            for pc in range(pb + 1, n):
                c = ordering[pc]
                if not ga[c]:
                    continue  # a not~ c
                if not triple_ok(a, b, c):
                    return False

    # Case 2: a is u or v (and b is neither, to avoid double work).
    for a in (u, v):
        pa = pos[a]
        ga = graph[a]
        for pb in range(pa + 1, n):
            b = ordering[pb]
            if b == u or b == v:
                continue
            if ga[b]:
                continue  # a~b
            Db = D[b]
            for pc in range(pb + 1, n):
                c = ordering[pc]
                if not ga[c]:
                    continue  # a not~ c
                if not triple_ok(a, b, c):
                    return False

    # Case 3: c is u or v (a, b neither).
    for c in (u, v):
        pc = pos[c]
        for pb in range(pc):
            b = ordering[pb]
            if b == u or b == v:
                continue
            for pa in range(pb):
                a = ordering[pa]
                if a == u or a == v:
                    continue
                if not graph[a][c]:
                    continue  # a not~ c
                if graph[a][b]:
                    continue  # a~b
                if not triple_ok(a, b, c):
                    return False

    return True


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    u, v = edge
    if _local_check(graph, ordering, u, v):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    u, v = edge
    if _local_check(graph, ordering, u, v):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
