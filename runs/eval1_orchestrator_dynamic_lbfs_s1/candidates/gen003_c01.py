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
    """Static LexBFS via partition refinement (HMPV), O(n^2).

    When a vertex v is output, EVERY class in the queue is refined by
    adjacency to v: each class C is split into C ∩ N(v) (placed before)
    and C \\ N(v) (placed after), preserving relative class order.

    Returns a list of n vertices in a valid LexBFS order.
    """
    adj = _adj_bitsets(graph, n)

    # Partition: list of classes, each class is a list of vertices.
    # Initially: one class containing all vertices, ordered by vertex id.
    # Queue: list of class indices, processed left to right.
    classes = [[v for v in range(n)]]
    q = [0]
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
        av = adj[v]

        # Collect all classes that must be refined by adjacency to v:
        # the remainder of the current class first (it was at the front),
        # then every other non-empty class in the queue in order.
        to_refine = []
        rest = cls[1:]
        if rest:
            to_refine.append(rest)
        for qi in range(head, len(q)):
            other = classes[q[qi]]
            if other:
                to_refine.append(other)

        # Split each class into neighbor / non-neighbor parts.
        new_q = []
        for c in to_refine:
            neigh = [x for x in c if (av >> x) & 1]
            non = [x for x in c if not ((av >> x) & 1)]
            if neigh:
                classes.append(neigh)
                new_q.append(len(classes) - 1)
            if non:
                classes.append(non)
                new_q.append(len(classes) - 1)

        # Clear the old classes that were consumed.
        classes[ci] = []
        for qi in range(head, len(q)):
            classes[q[qi]] = []

        # Rebuild the queue: processed prefix stays, new classes replace the rest.
        q = q[:head] + new_q

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
