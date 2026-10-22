"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder the affected vertex within its current
position range); if the repair fails, fall back to a full static
label-based LexBFS recompute.

The static LexBFS uses the standard label-based algorithm: each unprocessed
vertex carries the list of already-processed neighbors in processing order;
at each step the unprocessed vertex with the lexicographically smallest
label (tie-break: smallest vertex id) is selected.  This is a valid LexBFS.

Validity is certified by the (LB) 4-point property:
  for all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.
"""


def _lexbfs_full(graph):
    """Compute a valid LexBFS ordering from scratch using label-based LexBFS.

    Returns a list of vertex ids in LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    # Label for each vertex: list of processed neighbors in processing order
    labels = {v: [] for v in range(n)}
    # All vertices start with the same label (empty), so tie-break by id
    unprocessed = set(range(n))
    order = []
    while unprocessed:
        # Pick the unprocessed vertex with lexicographically smallest label,
        # tie-break by smallest vertex id
        v = min(unprocessed, key=lambda x: (labels[x], x))
        order.append(v)
        unprocessed.remove(v)
        # Update labels: append v to labels of unprocessed neighbors
        for u in unprocessed:
            if graph[v][u]:
                labels[u] = labels[u] + [v]
    return order


def _is_valid_lexbfs(order, graph):
    """Check if order is a valid LexBFS ordering using the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    if n == 0:
        return True

    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # ab in E, skip
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue  # ac not in E, skip
                # Need: exists d < a (pos[d] < pos[a]) with db in E and dc not in E
                found = False
                for l in range(i):
                    d = order[l]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_local_repair(order, graph, edge):
    """Try to repair the ordering locally after an edge update.

    Returns a new ordering if the repair succeeds, None otherwise.
    """
    u, v = edge
    n = len(order)

    # The edge (u, v) was added or removed.
    # The affected vertices are u and v.
    # Try to reorder u and v within the ordering to fix any violations.

    # Strategy: try all possible positions for u and v (swap, move, etc.)
    # and check if the result is valid.

    # First, try the current ordering as-is (maybe it's still valid).
    if _is_valid_lexbfs(order, graph):
        return order

    # Try swapping u and v
    if u != v:
        new_order = order[:]
        i = new_order.index(u)
        j = new_order.index(v)
        new_order[i], new_order[j] = new_order[j], new_order[i]
        if _is_valid_lexbfs(new_order, graph):
            return new_order

    # Try moving u to various positions
    for target in range(n):
        new_order = order[:]
        i = new_order.index(u)
        new_order.pop(i)
        new_order.insert(target, u)
        if _is_valid_lexbfs(new_order, graph):
            return new_order

    # Try moving v to various positions
    for target in range(n):
        new_order = order[:]
        i = new_order.index(v)
        new_order.pop(i)
        new_order.insert(target, v)
        if _is_valid_lexbfs(new_order, graph):
            return new_order

    # Try moving both u and v
    for target_u in range(n):
        new_order = order[:]
        i = new_order.index(u)
        new_order.pop(i)
        new_order.insert(target_u, u)
        for target_v in range(n):
            new_order2 = new_order[:]
            j = new_order2.index(v)
            new_order2.pop(j)
            new_order2.insert(target_v, v)
            if _is_valid_lexbfs(new_order2, graph):
                return new_order2

    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    n = len(graph)
    order = _lexbfs_full(graph)
    assert _is_valid_lexbfs(order, graph), "init produced invalid LexBFS"
    return {'ordering': order}


def insert_edge(graph, edge, state):
    """Handle an edge insertion."""
    order = state['ordering']
    n = len(order)

    # Try local repair first
    repaired = _try_local_repair(order, graph, edge)
    if repaired is not None:
        return {'ordering': repaired}

    # Fall back to full recompute
    order = _lexbfs_full(graph)
    assert _is_valid_lexbfs(order, graph), "insert_edge fallback produced invalid LexBFS"
    return {'ordering': order}


def delete_edge(graph, edge, state):
    """Handle an edge deletion."""
    order = state['ordering']
    n = len(order)

    # Try local repair first
    repaired = _try_local_repair(order, graph, edge)
    if repaired is not None:
        return {'ordering': repaired}

    # Fall back to full recompute
    order = _lexbfs_full(graph)
    assert _is_valid_lexbfs(order, graph), "delete_edge fallback produced invalid LexBFS"
    return {'ordering': order}
