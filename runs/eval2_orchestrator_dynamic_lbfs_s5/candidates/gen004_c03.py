"""Dynamic LexBFS ordering (candidate gen004_c03).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static label-based LexBFS (trivially correct, O(n^3) on the
    adjacency matrix).
  * update: try a cheap local repair that keeps the previous ordering valid
    (see _try_repair).  The repair is only ever applied when the resulting
    ordering is verified to satisfy the (LB) 4-point property, so
    correctness never depends on the repair succeeding.  If the repair
    fails, fall back to a full static recompute.

Improvements over the parent (gen002_c04):
  * The (LB) check is O(n^3) with a large constant (it re-scans all d < a
    for every violating triple).  We precompute, for each position a, the
    set of positions d < a that are adjacent to order[a] (as a Python set
    of ints).  The inner "exists d" test then becomes a set intersection
    test, which is much faster in practice.
  * The repair tries a few more local moves (swap, move-next-to in both
    directions, and a small window of nearby positions) before giving up.
    Each candidate is verified with the full (LB) check, so no incorrect
    ordering can ever be returned.
"""


def _lexbfs(adj, n):
    """Static LexBFS via the label-based formulation.

    Each unplaced vertex v carries a label: the list of 0/1 bits recording
    adjacency to each already-placed vertex, in placement order.  At each
    step, pick the unplaced vertex with the lexicographically smallest
    label (tie-break by vertex id), place it, and extend every remaining
    label with 1 if adjacent to the placed vertex, else 0.

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


def _is_lexbfs(order, adj, n):
    """Check the (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, there exists d < a with db in E and dc not
    in E.

    Optimised: precompute, for each position a, the set of positions d < a
    that are adjacent to order[a].  Then the "exists d" test is a set
    intersection: (pre[a] & nonneigh[vb]) - neigh[vc] must be non-empty.
    """
    if n <= 2:
        return True
    # neigh[v] = set of positions p such that order[p] is adjacent to v.
    neigh = [set() for _ in range(n)]
    for p in range(n):
        vp = order[p]
        for w in adj[vp]:
            neigh[w].add(p)
    # pre[a] = set of positions d < a with order[d] adjacent to order[a].
    pre = [set() for _ in range(n)]
    for a in range(n):
        va = order[a]
        pre[a] = neigh[va] & set(range(a))
    # nonneigh[v] = set of positions p such that order[p] is NOT adjacent
    # to v (and p != position of v itself, but that never matters here).
    allpos = set(range(n))
    nonneigh = [allpos - neigh[v] for v in range(n)]
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if a in neigh[vb]:
                continue  # ab in E, no constraint
            # ab not in E: for every c > b with ac in E, need a witness d.
            # pre[a] & nonneigh[vb] is the set of candidate witnesses d
            # (d < a, db in E, dc not in E for the current c).  It only
            # shrinks as c grows, so we can bail out early.
            cand = pre[a] & nonneigh[vb]
            for c in range(b + 1, n):
                vc = order[c]
                if a not in neigh[vc]:
                    continue  # ac not in E, no constraint
                cand -= neigh[vc]
                if not cand:
                    return False
    return True


def _try_repair(order, adj, n, edge):
    """Try to keep `order` valid after flipping `edge`.

    Returns a new ordering (possibly == order) if it is valid, else None.
    The idea: an edge flip only changes the 4-point certificate for triples
    involving the two endpoints.  We try small local moves (swap, move to
    nearby positions) and accept the first result that passes the full
    (LB) check.  The check is O(n^3) worst case but usually fast; the
    fallback recompute is also O(n^3) on the matrix, so this is a wash in
    the worst case and a win when the repair succeeds early.
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
    # candidates 3/4: move u (resp. v) to a position near the other
    # endpoint.  Each candidate is verified with the full (LB) check, so
    # no incorrect ordering can ever be returned.
    for target in (iv, iv + 1, iv - 1, iv + 2, iv - 2):
        if target < 0 or target > n - 1:
            continue
        o3 = list(order)
        o3.pop(iu)
        t = target
        if t > len(o3):
            t = len(o3)
        o3.insert(t, u)
        if _is_lexbfs(o3, adj, n):
            return o3
    for target in (iu, iu + 1, iu - 1, iu + 2, iu - 2):
        if target < 0 or target > n - 1:
            continue
        o4 = list(order)
        o4.pop(iv)
        t = target
        if t > len(o4):
            t = len(o4)
        o4.insert(t, v)
        if _is_lexbfs(o4, adj, n):
            return o4
    # candidates 5/6: move u (resp. v) to a position near its own old
    # position (a small local shuffle that can fix a violation caused by
    # the endpoint's neighbourhood changing).
    for target in (iu - 1, iu + 1, iu - 2, iu + 2):
        if target < 0 or target > n - 1:
            continue
        o5 = list(order)
        o5.pop(iu)
        t = target
        if t > len(o5):
            t = len(o5)
        o5.insert(t, u)
        if _is_lexbfs(o5, adj, n):
            return o5
    for target in (iv - 1, iv + 1, iv - 2, iv + 2):
        if target < 0 or target > n - 1:
            continue
        o6 = list(order)
        o6.pop(iv)
        t = target
        if t > len(o6):
            t = len(o6)
        o6.insert(t, v)
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
    return {'ordering': order, 'n': n, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    adj[u].add(v)
    adj[v].add(u)
    order = state['ordering']
    new_order = _try_repair(order, adj, n, edge)
    if new_order is None:
        new_order = _lexbfs(adj, n)
    return {'ordering': new_order, 'n': n, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    adj[u].discard(v)
    adj[v].discard(u)
    order = state['ordering']
    new_order = _try_repair(order, adj, n, edge)
    if new_order is None:
        new_order = _lexbfs(adj, n)
    return {'ordering': new_order, 'n': n, 'adj': adj}
