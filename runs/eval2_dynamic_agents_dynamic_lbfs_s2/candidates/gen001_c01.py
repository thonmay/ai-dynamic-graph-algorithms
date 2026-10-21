"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try a cheap
local repair (reorder a small window of the ordering to restore the (LB)
4-point property); if the repair fails, fall back to a full static
partition-refinement LexBFS recompute.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs_full(graph):
    """Static O(n^2 + n*m) LexBFS via partition refinement.

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []
    if n == 1:
        return [0]

    order = []
    # Partition of remaining vertices: list of sets
    partition = [set(range(n))]

    for _ in range(n):
        if not partition:
            break
        # Pick the first vertex from the first class (smallest for determinism)
        v = min(partition[0])
        order.append(v)
        partition[0].discard(v)

        # Refine partition by adjacency to v
        new_partition = []
        for C in partition:
            if not C:
                continue
            C_in = set(x for x in C if graph[v][x])
            C_out = C - C_in
            if C_in:
                new_partition.append(C_in)
            if C_out:
                new_partition.append(C_out)
        partition = new_partition

    return order


def _check_lb(order, graph):
    """Check the (LB) 4-point property. Returns True if valid."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue
            # ab not in E
            for k in range(j + 1, n):
                c = order[k]
                if graph[a][c] and not graph[b][c]:
                    # Need d < i with db in E and dc not in E
                    found = False
                    for d_idx in range(i):
                        d = order[d_idx]
                        if graph[d][b] and not graph[d][c]:
                            found = True
                            break
                    if not found:
                        return False
    return True


def _try_local_repair(order, graph, edge):
    """Try to repair the ordering locally after an edge update.

    Returns a new ordering if successful, None if the repair fails.
    """
    n = len(order)
    u, v = edge
    pos = {v: i for i, v in enumerate(order)}
    pu, pv = pos[u], pos[v]

    # Try: swap u and v
    new_order = order[:]
    new_order[pu], new_order[pv] = new_order[pv], new_order[pu]
    if _check_lb(new_order, graph):
        return new_order

    # Try: move u to just before v (if u is after v)
    if pu > pv:
        new_order = order[:]
        new_order.pop(pu)
        new_order.insert(pv, u)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move v to just before u (if v is after u)
    if pv > pu:
        new_order = order[:]
        new_order.pop(pv)
        new_order.insert(pu, v)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move u to just after v
    if pu < pv:
        new_order = order[:]
        new_order.pop(pu)
        new_order.insert(pv + 1, u)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move v to just after u
    if pv < pu:
        new_order = order[:]
        new_order.pop(pv)
        new_order.insert(pu + 1, v)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move u to position 0
    if pu != 0:
        new_order = order[:]
        new_order.pop(pu)
        new_order.insert(0, u)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move v to position 0
    if pv != 0:
        new_order = order[:]
        new_order.pop(pv)
        new_order.insert(0, v)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move u to the end
    if pu != n - 1:
        new_order = order[:]
        new_order.pop(pu)
        new_order.append(u)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move v to the end
    if pv != n - 1:
        new_order = order[:]
        new_order.pop(pv)
        new_order.append(v)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move u to each position (brute force over all positions)
    for target in range(n):
        if target == pu:
            continue
        new_order = order[:]
        new_order.pop(pu)
        new_order.insert(target, u)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move v to each position (brute force over all positions)
    for target in range(n):
        if target == pv:
            continue
        new_order = order[:]
        new_order.pop(pv)
        new_order.insert(target, v)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move both u and v to new positions (all pairs)
    # Remove u and v, then try all ways to insert them back
    remaining = [x for x in order if x != u and x != v]
    for i in range(n - 1):
        for j in range(n):
            if i == j:
                continue
            new_order = remaining[:]
            new_order.insert(i, u)
            new_order.insert(j, v)
            if _check_lb(new_order, graph):
                return new_order

    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    order = _lexbfs_full(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    """Handle an edge insertion. Return new state."""
    order = state['ordering']
    # Try local repair first
    new_order = _try_local_repair(order, graph, edge)
    if new_order is None:
        # Fall back to full recompute
        new_order = _lexbfs_full(graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    """Handle an edge deletion. Return new state."""
    order = state['ordering']
    # Try local repair first
    new_order = _try_local_repair(order, graph, edge)
    if new_order is None:
        # Fall back to full recompute
        new_order = _lexbfs_full(graph)
    return {'ordering': new_order}
