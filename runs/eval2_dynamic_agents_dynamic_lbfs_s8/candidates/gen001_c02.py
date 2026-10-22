"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try to repair
the existing ordering locally (cheap); if repair fails, fall back to a
full O(n^2) partition-refinement LexBFS recompute (always correct).

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
  for all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.
"""


def _check_valid(graph, order):
    """Check the LB 4-point property for `order` on `graph`. O(n^3)."""
    n = len(order)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    adj = [set() for _ in range(n)]
    for v in range(n):
        row = graph[v]
        for w in range(v + 1, n):
            if row[w]:
                adj[v].add(w)
                adj[w].add(v)
    for b in range(n):
        pb = pos[b]
        for c in range(n):
            if c == b:
                continue
            pc = pos[c]
            if pc <= pb:
                continue
            if b in adj[c]:
                continue  # need ab not in E
            # m = min pos[d] over d in adj[b] \ adj[c]
            m = None
            for d in adj[b]:
                if d not in adj[c]:
                    pd = pos[d]
                    if m is None or pd < m:
                        m = pd
            # m_a = min pos[a] over a in adj[c] with pos[a] < pb
            m_a = None
            for a in adj[c]:
                pa = pos[a]
                if pa < pb:
                    if m_a is None or pa < m_a:
                        m_a = pa
            if m_a is not None and m is not None and m_a <= m:
                return False
    return True


def _lexbfs_full(graph):
    """Full O(n^2) LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    adj = [set() for _ in range(n)]
    for v in range(n):
        row = graph[v]
        for w in range(v + 1, n):
            if row[w]:
                adj[v].add(w)
                adj[w].add(v)

    # Bucket-based LexBFS.
    # buckets: list of lists of vertices, in lexicographic label order.
    # Initially one bucket with all vertices.
    # At each step: pick first vertex of first non-empty bucket, refine all buckets.
    # After refinement by vertex v: for each bucket in order, the neighbor
    # part (_1) comes before the non-neighbor part (_0), and buckets maintain
    # their relative order.
    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        # Find first non-empty bucket
        first_idx = None
        for i, b in enumerate(buckets):
            if b:
                first_idx = i
                break
        if first_idx is None:
            break
        v = buckets[first_idx][0]
        buckets[first_idx] = buckets[first_idx][1:]
        order.append(v)
        # Refine all buckets by v
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            b1 = [x for x in b if x in adj[v]]
            b0 = [x for x in b if x not in adj[v]]
            if b1:
                new_buckets.append(b1)
            if b0:
                new_buckets.append(b0)
        buckets = new_buckets
    return order


def _try_repair_insert(graph, order, u, v):
    """Try to repair ordering after inserting edge (u,v). Returns new order or None."""
    n = len(order)
    pos = {vertex: i for i, vertex in enumerate(order)}
    pu, pv = pos[u], pos[v]
    if abs(pu - pv) == 1:
        return order
    # Try moving v to be just before u
    new_order = order[:pu] + [v] + order[pu:pv] + order[pv + 1:]
    if _check_valid(graph, new_order):
        return new_order
    # Try moving v to be just after u
    new_order = order[:pu + 1] + [v] + order[pu + 1:pv] + order[pv + 1:]
    if _check_valid(graph, new_order):
        return new_order
    # Try moving u to be just before v
    new_order = order[:pv] + [u] + order[pv:pu] + order[pu + 1:]
    if _check_valid(graph, new_order):
        return new_order
    # Try moving u to be just after v
    new_order = order[:pv + 1] + [u] + order[pv + 1:pu] + order[pu + 1:]
    if _check_valid(graph, new_order):
        return new_order
    return None


def _try_repair_delete(graph, order, u, v):
    """Try to repair ordering after deleting edge (u,v). Returns new order or None."""
    n = len(order)
    pos = {vertex: i for i, vertex in enumerate(order)}
    pu, pv = pos[u], pos[v]
    if abs(pu - pv) != 1:
        return order
    # Try swapping u and v
    new_order = list(order)
    new_order[pu], new_order[pv] = new_order[pv], new_order[pu]
    if _check_valid(graph, new_order):
        return new_order
    # Try moving v to be just before u
    if pu < pv:
        new_order = order[:pu] + [v] + order[pu:pv] + order[pv + 1:]
        if _check_valid(graph, new_order):
            return new_order
    else:
        new_order = order[:pu + 1] + [v] + order[pu:pv + 1] + order[pv + 1:]
        if _check_valid(graph, new_order):
            return new_order
    # Try moving u to be just before v
    if pu < pv:
        new_order = order[:pv] + [u] + order[pv:pu] + order[pu + 1:]
        if _check_valid(graph, new_order):
            return new_order
    else:
        new_order = order[:pu] + [u] + order[pu:pv] + order[pv + 1:]
        if _check_valid(graph, new_order):
            return new_order
    # Try moving u to be just after v
    if pu < pv:
        new_order = order[:pv + 1] + [u] + order[pv + 1:pu] + order[pu + 1:]
        if _check_valid(graph, new_order):
            return new_order
    else:
        new_order = order[:pu + 1] + [u] + order[pu:pv + 1] + order[pv + 1:]
        if _check_valid(graph, new_order):
            return new_order
    return None


def init(graph):
    n = len(graph)
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    new_order = _try_repair_insert(graph, order, u, v)
    if new_order is None:
        new_order = _lexbfs_full(graph)
    state['ordering'] = new_order
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    new_order = _try_repair_delete(graph, order, u, v)
    if new_order is None:
        new_order = _lexbfs_full(graph)
    state['ordering'] = new_order
    return state
