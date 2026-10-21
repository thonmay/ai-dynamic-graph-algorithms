"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder the affected vertex within its current
position range); if the repair fails the (LB) 4-point certificate,
fall back to a full O(n^2) LexBFS recompute.

The (LB) certificate (Corneil & Krueger): for all positions a < b < c
with ac in E and ab not in E, there exists d < a with db in E and
dc not in E.
"""


def _n_of(graph):
    return len(graph)


def _adj_bitsets(graph, n):
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        b = 0
        for v in range(n):
            if row[v]:
                b |= 1 << v
        adj[u] = b
    return adj


def _lexbfs(graph, n):
    """Static LexBFS via partition refinement, O(n^2).

    Returns a list of n vertices in a valid LexBFS order.
    """
    adj = _adj_bitsets(graph, n)

    # Partition: list of classes, each class is a list of vertices.
    # Initially: one class per vertex, ordered by vertex id.
    # Queue: list of class indices, processed left to right.
    # When we process a class, we output its first vertex, then split
    # the rest by adjacency to that vertex.

    classes = [[v] for v in range(n)]
    q = list(range(n))
    head = 0
    result = []

    while head < len(q):
        ci = q[head]
        head += 1
        cls = classes[ci]
        if not cls:
            continue
        v = cls[0]
        result.append(v)
        if len(cls) == 1:
            classes[ci] = []
            continue
        # Split cls[1:] by adjacency to v
        av = adj[v]
        neigh = []
        non = []
        for x in cls[1:]:
            if (av >> x) & 1:
                neigh.append(x)
            else:
                non.append(x)
        classes[ci] = []
        # Insert new classes at position head in the queue
        insert_pos = head
        if neigh:
            classes.append(neigh)
            q.insert(insert_pos, len(classes) - 1)
            insert_pos += 1
        if non:
            classes.append(non)
            q.insert(insert_pos, len(classes) - 1)

    return result


def _check_lb(graph, n, ordering):
    """Check the (LB) 4-point property. Returns True if valid."""
    if n <= 2:
        return True

    adj = _adj_bitsets(graph, n)

    # pos_mask[p] = bitmask of vertices at positions < p
    pos_mask = [0] * (n + 1)
    m = 0
    for i in range(n):
        pos_mask[i] = m
        m |= 1 << ordering[i]
    pos_mask[n] = m

    for pb in range(n):
        b = ordering[pb]
        for pa in range(pb):
            a = ordering[pa]
            if (adj[a] >> b) & 1:
                continue  # ab in E, no constraint
            # C = vertices after b that are neighbors of a
            C = adj[a] & ~pos_mask[pb + 1]
            if C == 0:
                continue
            # D = vertices before a that are neighbors of b
            D = adj[b] & pos_mask[pa]
            if D == 0:
                return False
            # Check: exists d in D such that (adj[d] & C) != C
            d_mask = D
            while d_mask:
                lb = d_mask & (-d_mask)
                d = lb.bit_length() - 1
                d_mask ^= lb
                if (adj[d] & C) != C:
                    break  # found valid d
            else:
                return False  # all d in D are adjacent to all c in C
    return True


def _local_repair(graph, n, ordering, edge):
    """Try to repair the ordering after an edge update.

    Returns a new ordering if valid, else None.
    """
    u, v = edge

    # First: is the current ordering still valid?
    if _check_lb(graph, n, ordering):
        return ordering

    # Try swapping u and v
    if u != v:
        new_order = ordering[:]
        pu = new_order.index(u)
        pv = new_order.index(v)
        new_order[pu], new_order[pv] = new_order[pv], new_order[pu]
        if _check_lb(graph, n, new_order):
            return new_order

    # Try moving u to each position
    for target in range(n):
        if target == ordering.index(u):
            continue
        new_order = ordering[:]
        new_order.remove(u)
        new_order.insert(target, u)
        if _check_lb(graph, n, new_order):
            return new_order

    # Try moving v to each position
    for target in range(n):
        if target == ordering.index(v):
            continue
        new_order = ordering[:]
        new_order.remove(v)
        new_order.insert(target, v)
        if _check_lb(graph, n, new_order):
            return new_order

    # Try moving both u and v
    for tu in range(n):
        new_order = ordering[:]
        new_order.remove(u)
        new_order.insert(tu, u)
        for tv in range(n):
            if tv == new_order.index(v):
                continue
            new_order2 = new_order[:]
            new_order2.remove(v)
            new_order2.insert(tv, v)
            if _check_lb(graph, n, new_order2):
                return new_order2

    return None


def init(graph):
    n = _n_of(graph)
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    ordering = state['ordering']
    new_order = _local_repair(graph, n, ordering, edge)
    if new_order is None:
        new_order = _lexbfs(graph, n)
    return {'ordering': new_order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    ordering = state['ordering']
    new_order = _local_repair(graph, n, ordering, edge)
    if new_order is None:
        new_order = _lexbfs(graph, n)
    return {'ordering': new_order, 'n': n}
