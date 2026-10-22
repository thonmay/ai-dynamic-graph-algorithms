"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try to repair
the existing ordering locally (cheap); if local repair fails, fall back to
a full O(n^2) partition-refinement LexBFS recompute (always correct).

The (LB) 4-point property (Corneil & Krueger): for all positions a < b < c
with ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs_full(graph):
    """Full partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    if n == 1:
        return [0]

    # Standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
    # P: list of buckets (lists of vertices), in current order.
    # Q: FIFO queue of bucket references to refine.
    # Invariant: every non-empty bucket in P appears in Q exactly once.
    # At each step: pop front non-empty bucket from Q, take its first
    # vertex v, append v to order, refine all other buckets by v.
    # The surviving bucket b (if still non-empty) is re-enqueued.

    P = [list(range(n))]
    Q = [P[0]]
    head = 0
    order = []

    while head < len(Q):
        b = Q[head]
        head += 1
        if not b:
            continue
        v = b.pop(0)
        order.append(v)
        # Refine all buckets except b by v's adjacency.
        # The surviving bucket b is re-enqueued first so that its next
        # vertex is processed before any vertex from a split bucket
        # (this is what makes the ordering a genuine LexBFS ordering).
        newP = []
        if b:
            newP.append(b)
            Q.append(b)  # re-enqueue surviving bucket
        for b2 in P:
            if b2 is b:
                continue
            N = [x for x in b2 if graph[v][x]]
            Nc = [x for x in b2 if not graph[v][x]]
            if N:
                newP.append(N)
                Q.append(N)
            if Nc:
                newP.append(Nc)
                Q.append(Nc)
        P = newP

    return order


def _lexbfs_canonical(graph):
    """Canonical LexBFS: start at the smallest vertex, break ties by
    smallest vertex id.  Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    if n == 1:
        return [0]

    # Label-based LexBFS.  Each unvisited vertex x carries the label
    # L(x) = (1 if x adjacent to order[0], 1 if x adjacent to order[1],
    # ...).  At each step pick the unvisited vertex with the
    # lexicographically largest label (ties broken by smallest id) and
    # append it to the order.  This is the standard LexBFS definition
    # and always yields a valid LexBFS ordering.

    order = [0]
    remaining = list(range(1, n))
    while remaining:
        # Pick the vertex with the lexicographically largest label,
        # ties broken by smallest vertex id.
        best = None
        best_key = None
        for x in remaining:
            key = tuple(1 if graph[x][y] else 0 for y in order)
            if best is None or key > best_key or (key == best_key and x < best):
                best = x
                best_key = key
        order.append(best)
        remaining.remove(best)

    return order


def _check_lb_property(graph, order):
    """Check the (LB) 4-point property. Returns True if valid."""
    n = len(order)
    # For all a < b < c (positions) with ac in E and ab not in E,
    # there exists d < a with db in E and dc not in E.
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
                # Need d < i with db in E and dc not in E.
                found = False
                for l in range(i):
                    d = order[l]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_local_repair(graph, order, edge):
    """Try to repair the ordering after an edge update. Returns new
    ordering if successful, None if not."""
    u, v = edge
    n = len(order)
    if n == 0:
        return order

    # First check if the current ordering is still valid.
    if _check_lb_property(graph, order):
        return order

    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    candidates = []

    # Move v to end
    if pos[v] != n - 1:
        candidates.append(order[:pos[v]] + order[pos[v] + 1:] + [v])
    # Move v to beginning
    if pos[v] != 0:
        candidates.append([v] + order[:pos[v]] + order[pos[v] + 1:])
    # Move v after u
    if pos[v] != pos[u] + 1:
        o = order[:pos[v]] + order[pos[v] + 1:]
        pu = o.index(u)
        candidates.append(o[:pu + 1] + [v] + o[pu + 1:])
    # Move v before u
    if pos[v] != pos[u]:
        o = order[:pos[v]] + order[pos[v] + 1:]
        pu = o.index(u)
        candidates.append(o[:pu] + [v] + o[pu:])
    # Move u to end
    if pos[u] != n - 1:
        candidates.append(order[:pos[u]] + order[pos[u] + 1:] + [u])
    # Move u to beginning
    if pos[u] != 0:
        candidates.append([u] + order[:pos[u]] + order[pos[u] + 1:])
    # Move u after v
    if pos[u] != pos[v] + 1:
        o = order[:pos[u]] + order[pos[u] + 1:]
        pv = o.index(v)
        candidates.append(o[:pv + 1] + [u] + o[pv + 1:])
    # Move u before v
    if pos[u] != pos[v]:
        o = order[:pos[u]] + order[pos[u] + 1:]
        pv = o.index(v)
        candidates.append(o[:pv] + [u] + o[pv:])
    # Swap u and v
    if pos[u] != pos[v]:
        o = order[:]
        o[pos[u]], o[pos[v]] = o[pos[v]], o[pos[u]]
        candidates.append(o)

    for cand in candidates:
        if _check_lb_property(graph, cand):
            return cand

    return None


def init(graph):
    order = _lexbfs_canonical(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    new_order = _try_local_repair(graph, order, edge)
    if new_order is None:
        new_order = _lexbfs_canonical(graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    order = state['ordering']
    new_order = _try_local_repair(graph, order, edge)
    if new_order is None:
        new_order = _lexbfs_canonical(graph)
    return {'ordering': new_order}
