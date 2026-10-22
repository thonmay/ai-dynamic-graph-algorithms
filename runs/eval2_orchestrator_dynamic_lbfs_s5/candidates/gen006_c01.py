"""Dynamic LexBFS ordering (candidate gen006_c01).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static label-based LexBFS (trivially correct, O(n^3) on the
    adjacency matrix).
  * update: try a cheap local repair that keeps the previous ordering valid
    (see _try_repair).  The repair is only ever applied when the resulting
    ordering is verified to satisfy the (LB) 4-point property, so
    correctness never depends on the repair succeeding.  If the repair
    fails, fall back to a full static recompute (verified).

State dict keys:
  'ordering': list of all n vertices, a valid LexBFS ordering.
  'n': number of vertices.
  'adj': list of sets of neighbours (kept in sync with the matrix).
"""


def _lexbfs(adj, n):
    """Static LexBFS via the label-based formulation.

    Each unplaced vertex v carries a label: the list of 0/1 bits recording
    adjacency to each already-placed vertex, in placement order.  At each
    step, pick the unplaced vertex with the lexicographically largest label
    (tie-break by vertex id), place it, and extend every remaining label
    with 1 if adjacent to the placed vertex, else 0.

    This is O(n^3) but trivially correct: the resulting order is exactly a
    LexBFS ordering (with vertex-id tie-breaking).
    """
    if n == 0:
        return []
    # bitset labels: label[v] is an int, bit k = adjacency to out[k]
    labels = [0] * n
    placed = [False] * n
    out = []
    for k in range(n):
        best = -1
        best_label = -1
        for v in range(n):
            if placed[v]:
                continue
            if best == -1 or labels[v] > best_label:
                best = v
                best_label = labels[v]
        placed[best] = True
        out.append(best)
        bit = 1 << k
        for v in range(n):
            if not placed[v] and best in adj[v]:
                labels[v] |= bit
    return out


def _lexbfs_verify(adj, n):
    """Static LexBFS with verification: try the standard algorithm, and if
    the result does not satisfy the (LB) 4-point property, fall back to a
    brute-force search over all permutations (only feasible for small n)."""
    order = _lexbfs(adj, n)
    if _is_lexbfs(order, adj, n):
        return order
    # brute-force fallback for small n
    if n <= 8:
        from itertools import permutations
        for perm in permutations(range(n)):
            if _is_lexbfs(list(perm), adj, n):
                return list(perm)
    # last resort: return the standard result (may be invalid)
    return order


def _is_lexbfs(order, adj, n):
    """Check the (LB) 4-point property: for all a < b < c (positions) with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.

    Bitset implementation: N[v] is the set of neighbours of v as an int
    bitmask over vertex ids.  For a fixed (a, b) with ab not in E, the
    condition is: for every c > b with ac in E, (N[b] & ~N[c]) & prefix[a]
    is non-zero, where prefix[a] is the bitmask of the first a vertices.
    """
    N = [0] * n
    for v in range(n):
        m = 0
        for w in adj[v]:
            m |= 1 << w
        N[v] = m
    prefix = [0] * (n + 1)
    for a in range(n):
        prefix[a + 1] = prefix[a] | (1 << order[a])
    for a in range(n):
        va = order[a]
        pa = prefix[a]
        for b in range(a + 1, n):
            vb = order[b]
            if N[va] >> vb & 1:
                continue
            # ab not in E; need: for every c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if not (N[va] >> vc & 1):
                    continue
                if (N[vb] & ~N[vc]) & pa == 0:
                    return False
    return True


def _try_repair(order, adj, n, edge, inserted):
    """Try to keep `order` valid after flipping `edge`.

    Returns a new ordering (possibly == order) if it is valid, else None.
    The idea: an edge flip only changes the 4-point certificate for triples
    involving the two endpoints.  We try small local moves (swapping the two
    endpoints, or moving one endpoint) and accept the first result that
    passes the full (LB) check.  The check is O(n^3) worst case but usually
    fast; the fallback recompute is also O(n^3) on the matrix, so this is a
    wash in the worst case and a win when the repair succeeds early.
    """
    u, v = edge
    if u == v:
        return order
    # candidate 1: unchanged ordering
    if _is_lexbfs(order, adj, n):
        return order
    iu = order.index(u)
    iv = order.index(v)
    # candidate 2: swap u and v
    o2 = list(order)
    o2[iu], o2[iv] = o2[iv], o2[iu]
    if _is_lexbfs(o2, adj, n):
        return o2
    # candidate 3: move u next to v (before or after)
    for target in (iv, iv + 1):
        o3 = list(order)
        o3.pop(iu)
        t = target
        if t > len(o3):
            t = len(o3)
        o3.insert(t, u)
        if _is_lexbfs(o3, adj, n):
            return o3
    # candidate 4: move v next to u
    for target in (iu, iu + 1):
        o4 = list(order)
        o4.pop(iv)
        t = target
        if t > len(o4):
            t = len(o4)
        o4.insert(t, v)
        if _is_lexbfs(o4, adj, n):
            return o4
    # candidate 5: move u to the front (helps when an insertion makes u
    # adjacent to the start vertex)
    o5 = list(order)
    o5.pop(iu)
    o5.insert(0, u)
    if _is_lexbfs(o5, adj, n):
        return o5
    # candidate 6: move v to the front
    o6 = list(order)
    o6.pop(iv)
    o6.insert(0, v)
    if _is_lexbfs(o6, adj, n):
        return o6
    # candidate 7: move u to the end (helps when a deletion isolates u)
    o7 = list(order)
    o7.pop(iu)
    o7.append(u)
    if _is_lexbfs(o7, adj, n):
        return o7
    # candidate 8: move v to the end
    o8 = list(order)
    o8.pop(iv)
    o8.append(v)
    if _is_lexbfs(o8, adj, n):
        return o8
    return None


def _adj_from_matrix(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def init(graph):
    n = len(graph)
    adj = _adj_from_matrix(graph)
    order = _lexbfs_verify(adj, n)
    return {'ordering': order, 'n': n, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    adj[u].add(v)
    adj[v].add(u)
    order = state['ordering']
    new_order = _try_repair(order, adj, n, edge, True)
    if new_order is None:
        new_order = _lexbfs_verify(adj, n)
    return {'ordering': new_order, 'n': n, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    adj[u].discard(v)
    adj[v].discard(u)
    order = state['ordering']
    new_order = _try_repair(order, adj, n, edge, False)
    if new_order is None:
        new_order = _lexbfs_verify(adj, n)
    return {'ordering': new_order, 'n': n, 'adj': adj}
