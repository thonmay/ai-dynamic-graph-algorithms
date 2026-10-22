"""Dynamic LexBFS ordering (candidate gen001_c04).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n^2) on the adjacency matrix.
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
    """Static LexBFS via partition refinement.  adj: list of sets.

    Uses the standard bucket-list formulation:
      - maintain a list of buckets (ordered sets of vertices)
      - for each vertex x in the order it is removed from its bucket:
          * split every other bucket into (N(x), N(x)^c) parts
          * x's own bucket is split into ({x}, N(x)∩B, N(x)^c∩B)
          * x is placed in a new first bucket
    """
    # buckets: list of lists of vertices, in current order
    buckets = [[v] for v in range(n)]
    # pos[v] = index of the bucket containing v
    pos = list(range(n))
    # order: list of bucket indices in current order
    order = list(range(n))

    for x in range(n):
        # find the bucket containing x
        bx = pos[x]
        # remove bucket bx from order
        order.pop(bx)
        # refine every bucket by adjacency to x
        new_buckets = []
        for bi in order:
            B = buckets[bi]
            N = []
            Nn = []
            for v in B:
                if x in adj[v]:
                    N.append(v)
                else:
                    Nn.append(v)
            if N:
                new_buckets.append(N)
            if Nn:
                new_buckets.append(Nn)
        # x's own bucket: x first, then its neighbours, then non-neighbours
        Bx = buckets[bx]
        rest = [v for v in Bx if v != x]
        N = [v for v in rest if x in adj[v]]
        Nn = [v for v in rest if x not in adj[v]]
        # x goes to the front, then N, then Nn
        new_buckets.insert(0, [x])
        if N:
            new_buckets.insert(1, N)
        if Nn:
            new_buckets.insert(2 if N else 1, Nn)
        buckets = new_buckets
        # recompute pos
        pos = [0] * n
        for bi, B in enumerate(buckets):
            for v in B:
                pos[v] = bi
        order = list(range(len(buckets)))

    # flatten
    out = []
    for bi in order:
        out.extend(buckets[bi])
    return out


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
    order = _lexbfs(adj, n)
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
    return {'ordering': new_order, 'n': n, 'adj': adj}
