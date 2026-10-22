"""Dynamic LexBFS ordering (candidate gen004_c02).

Strategy: maintain a valid LexBFS ordering under single edge flips.

- init: static label-based LexBFS, O(n^3) with adjacency matrix.
- insert_edge: try a local repair (move one of the two endpoints); if that
  fails, fall back to a full recompute.
- delete_edge: recompute from scratch.

The (LB) property: for all a < b < c in the ordering with ac in E and
ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph, start=0):
    """Static LexBFS via the label (non-neighbor) formulation.

    Each unprocessed vertex keeps the list of already-processed vertices
    that are NOT its neighbors; the next vertex is the one with the
    lexicographically smallest such list.  This is the direct, trivially
    correct formulation of LexBFS (no bucket-ordering subtleties).
    """
    n = len(graph)
    if n == 0:
        return []
    nbrs = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if row[j]:
                nbrs[i].add(j)
    labels = {v: [] for v in range(n)}
    ordering = [start]
    remaining = set(range(n)) - {start}
    for v in remaining:
        if v not in nbrs[start]:
            labels[v].append(start)
    for _ in range(n - 1):
        best = min(remaining, key=lambda v: labels[v])
        ordering.append(best)
        remaining.remove(best)
        for v in remaining:
            if v not in nbrs[best]:
                labels[v].append(best)
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
