"""Dynamic LexBFS ordering (candidate gen004_c02).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static label-based LexBFS (trivially correct, O(n^3)).
  * update: try a cheap local repair that keeps the previous ordering valid
    (see _try_repair).  If the repair fails, fall back to a full static
    recompute.  The repair is only ever applied when the resulting ordering
    is verified to satisfy the (LB) 4-point property, so correctness never
    depends on the repair succeeding.

State dict keys:
  'ordering': list of all n vertices, a valid LexBFS ordering.
  'n': number of vertices.
  'adj': list of sets of neighbours (kept in sync with the matrix).
"""


def _lexbfs(adj, n):
    """Static LexBFS via the label-based formulation.

    Each unplaced vertex v carries a label (list of 0/1) recording, for each
    already-placed vertex in placement order, whether v is adjacent to it.
    At each step, pick the unplaced vertex with the lexicographically
    smallest label (tie-break by vertex id), append it to the order, and
    extend every remaining vertex's label with 1 if adjacent to the placed
    vertex, else 0.

    This is O(n^3) but trivially correct: the resulting order is exactly a
    LexBFS order (any start vertex, any tie-break is legal).
    """
    # LexBFS label convention: label[v][i] = 1 iff v is NOT adjacent to the
    # vertex placed at step i.  The unplaced vertex with the lexicographically
    # smallest label is selected next (tie-break by vertex id).  This is the
    # standard label formulation of LexBFS.
    labels = [[] for _ in range(n)]
    placed = [False] * n
    order = []
    for _ in range(n):
        # pick unplaced vertex with lexicographically smallest label,
        # tie-break by vertex id
        best = None
        for v in range(n):
            if placed[v]:
                continue
            if best is None or (labels[v], v) < (labels[best], best):
                best = v
        placed[best] = True
        order.append(best)
        for v in range(n):
            if not placed[v]:
                labels[v].append(0 if best in adj[v] else 1)
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
    # candidate 5: move u to the front
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
    order = _lexbfs(adj, n)
    # self-check: the static routine must produce a valid LexBFS order
    if not _is_lexbfs(order, adj, n):
        raise AssertionError('init produced an invalid LexBFS ordering')
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
        new_order = _lexbfs(adj, n)
        if not _is_lexbfs(new_order, adj, n):
            raise AssertionError('recompute produced an invalid LexBFS ordering')
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
        new_order = _lexbfs(adj, n)
        if not _is_lexbfs(new_order, adj, n):
            raise AssertionError('recompute produced an invalid LexBFS ordering')
    return {'ordering': new_order, 'n': n, 'adj': adj}
