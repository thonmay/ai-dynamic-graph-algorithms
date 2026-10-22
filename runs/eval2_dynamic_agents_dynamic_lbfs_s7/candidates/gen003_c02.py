"""Dynamic LexBFS ordering (candidate gen003_c02).

Strategy: maintain a valid LexBFS ordering under single edge flips.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n^2) with adjacency matrix.
- insert_edge: try a local repair (move one of the two endpoints); if that
  fails, try a full recompute with a different start vertex.
- delete_edge: recompute from scratch.

The (LB) property: for all a < b < c in the ordering with ac in E and
ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph, start=None):
    """Static LexBFS via partition refinement (HMPV). Returns ordering list.
    If start is None, uses vertex 0. Otherwise uses the given vertex."""
    n = len(graph)
    if n == 0:
        return []
    if start is None:
        start = 0

    # for each vertex, the set of neighbors (as a set for O(1) lookup)
    nbrs = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if row[j]:
                nbrs[i].add(j)

    # Queue of buckets; start first, rest in id order
    buckets = [[start]] + [[v] for v in range(n) if v != start]
    ordering = []
    for _ in range(n):
        # Find front non-empty bucket
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        # Select vertex from front bucket (any tie-break; use min id)
        v = min(buckets[bi])
        buckets[bi].remove(v)
        ordering.append(v)
        # Refine every bucket by adjacency to v
        new_buckets = []
        tail = []
        for B in buckets:
            if not B:
                continue
            B1 = [x for x in B if x in nbrs[v]]
            B2 = [x for x in B if x not in nbrs[v]]
            if B1:
                new_buckets.append(B1)
            if B2:
                tail.append(B2)
        buckets = new_buckets + tail
    return ordering


def _is_valid_lexbfs(ordering, graph):
    """Check the (LB) 4-point property. Returns True if valid."""
    n = len(ordering)
    if n == 0:
        return True
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if row[j]:
                adj[i].add(j)
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if vb in adj[va]:
                continue  # ab in E, condition not triggered
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E
            for c in range(b + 1, n):
                vc = ordering[c]
                if vc not in adj[va]:
                    continue  # ac not in E
                # need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if vb in adj[vd] and vc not in adj[vd]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_repair_insert(ordering, graph, u, v):
    """Try to repair the ordering after inserting edge (u, v).

    Inserting an edge can only destroy witnesses (dc not in E becomes
    dc in E). Check if ordering is still valid; if not, try moving u or v.
    """
    if _is_valid_lexbfs(ordering, graph):
        return ordering
    n = len(ordering)
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i

    # Try moving u to each position
    for target in range(n):
        if target == pos[u]:
            continue
        new_order = list(ordering)
        new_order.pop(pos[u])
        new_order.insert(target, u)
        if _is_valid_lexbfs(new_order, graph):
            return new_order
    # Try moving v to each position
    for target in range(n):
        if target == pos[v]:
            continue
        new_order = list(ordering)
        new_order.pop(pos[v])
        new_order.insert(target, v)
        if _is_valid_lexbfs(new_order, graph):
            return new_order
    return None


def _recompute(graph):
    """Full recompute: try start=0 first, then other starts if needed."""
    n = len(graph)
    if n == 0:
        return []
    # Try start=0
    ordering = _lexbfs(graph, start=0)
    if _is_valid_lexbfs(ordering, graph):
        return ordering
    # Try other starts
    for s in range(1, n):
        ordering = _lexbfs(graph, start=s)
        if _is_valid_lexbfs(ordering, graph):
            return ordering
    # Should not reach here; return the first one
    return _lexbfs(graph, start=0)


def init(graph):
    ordering = _recompute(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    # The harness passes the post-update matrix (the edge is already set).
    # Do not mutate the caller's matrix.
    g = [row[:] for row in graph]
    ordering = state['ordering']
    # Try local repair first
    repaired = _try_repair_insert(ordering, g, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute
    return {'ordering': _recompute(g)}


def delete_edge(graph, edge, state):
    # The harness passes the post-update matrix (the edge is already cleared).
    # Do not mutate the caller's matrix.
    g = [row[:] for row in graph]
    # Deletion can break the (LB) property; recompute from scratch.
    return {'ordering': _recompute(g)}
