"""Dynamic LexBFS ordering (candidate gen003_c01).

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
    labels = [[] for _ in range(n)]
    placed = [False] * n
    out = []
    for _ in range(n):
        best = -1
        for v in range(n):
            if placed[v]:
                continue
            if best == -1 or labels[v] > labels[best]:
                best = v
        placed[best] = True
        out.append(best)
        for v in range(n):
            if not placed[v]:
                labels[v].append(1 if best in adj[v] else 0)
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
    ac in E and ab not in E, exists d < a with db in E and dc not in E."""
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if va in adj[vb]:
                continue
            # ab not in E; need: for every c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if va not in adj[vc]:
                    continue
                ok = False
                for d in range(a):
                    vd = order[d]
                    if vb in adj[vd] and vc not in adj[vd]:
                        ok = True
                        break
                if not ok:
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
    # candidate 2: swap u and v
    o2 = list(order)
    iu = o2.index(u)
    iv = o2.index(v)
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
