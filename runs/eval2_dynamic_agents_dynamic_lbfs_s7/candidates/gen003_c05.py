"""Dynamic LexBFS ordering (candidate gen003_c05).

Strategy: maintain a valid LexBFS ordering under single edge flips.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n^2) with adjacency matrix.
- insert_edge: check if the old ordering is still valid (insertion can only
  destroy witnesses); if not, try moving one of the two endpoints to each
  position; if that fails, full recompute.
- delete_edge: check if the old ordering is still valid (deletion can only
  create witnesses); if not, try moving one of the two endpoints to each
  position; if that fails, full recompute.

The (LB) property: for all a < b < c in the ordering with ac in E and
ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph, start=None):
    """Static LexBFS via partition refinement. Returns ordering list.
    If start is None, uses vertex 0. Otherwise uses the given vertex."""
    n = len(graph)
    if n == 0:
        return []
    if start is None:
        start = 0

    # buckets: list of lists of vertices, in order
    # start vertex goes first, then the rest in id order
    buckets = [[start]]
    for v in range(n):
        if v != start:
            buckets.append([v])
    # for each vertex, the index of its bucket
    bidx = [0] * n
    for bi, B in enumerate(buckets):
        for v in B:
            bidx[v] = bi
    # for each vertex, the set of neighbors (as a set for O(1) lookup)
    nbrs = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if row[j]:
                nbrs[i].add(j)

    for x in range(n):
        # find bucket of x
        bx = bidx[x]
        # refine: for each bucket B != bx, split into B∩N(x) and B\N(x)
        # process buckets in order; new buckets keep relative order
        new_buckets = []
        for bi, B in enumerate(buckets):
            if bi == bx:
                new_buckets.append(B)
                continue
            B1 = [v for v in B if v in nbrs[x]]
            B2 = [v for v in B if v not in nbrs[x]]
            if B1:
                new_buckets.append(B1)
            if B2:
                new_buckets.append(B2)
        buckets = new_buckets
        # update bidx
        for bi, B in enumerate(buckets):
            for v in B:
                bidx[v] = bi

    # ordering: vertices in bucket order, within bucket by original id
    ordering = []
    for B in buckets:
        ordering.extend(sorted(B))
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


def _try_repair(ordering, graph, u, v):
    """Try to repair the ordering after a single edge flip.

    Check if ordering is still valid; if not, try moving u or v to each
    position. Returns the repaired ordering or None.
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
    repaired = _try_repair(ordering, g, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute
    return {'ordering': _recompute(g)}


def delete_edge(graph, edge, state):
    u, v = edge
    # The harness passes the post-update matrix (the edge is already cleared).
    # Do not mutate the caller's matrix.
    g = [row[:] for row in graph]
    ordering = state['ordering']
    # Try local repair first (deletion can only create witnesses, so the
    # old ordering is often still valid)
    repaired = _try_repair(ordering, g, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute
    return {'ordering': _recompute(g)}
