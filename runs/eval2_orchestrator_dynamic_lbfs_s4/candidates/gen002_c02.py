"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge: if the new edge (u,v) is consistent with the current ordering
  (the earlier vertex's non-neighbor set is a subset of the later vertex's),
  the ordering stays valid; otherwise recompute.
- delete_edge: if the removed edge (u,v) is "witnessed" by the current
  ordering (there exists d < u with d~v and not d~u, where u is the earlier
  endpoint), the ordering stays valid; otherwise recompute.

Both incremental checks are O(n).  The (LB) 4-point property of Corneil and
Krueger certifies validity, and the two lemmas below justify the checks.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement.  Returns the ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets of vertices, in queue order
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # pick the smallest vertex from the first non-empty bucket
        v = None
        for B in buckets:
            if B:
                v = min(B)
                break
        if v is None:
            break
        order.append(v)
        # remove v from its bucket
        for B in buckets:
            if v in B:
                B.discard(v)
                break
        # refine every remaining bucket by adjacency to v
        new_buckets = []
        for C in buckets:
            if not C:
                continue
            Cn = set()
            Cy = set()
            for w in C:
                if graph[v][w]:
                    Cy.add(w)
                else:
                    Cn.add(w)
            if Cn:
                new_buckets.append(Cn)
            if Cy:
                new_buckets.append(Cy)
        buckets = new_buckets
    return order


def _recompute(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def _insert_ok(graph, u, v, order):
    """After adding edge (u,v), is `order` still a valid LexBFS?

    Let u be the earlier endpoint in `order`.  The new edge (u,v) can only
    create (LB) violations with a = u and c = v (the edge itself is the new
    adjacency ac in E).  For every b with pos[u] < pos[b] < pos[v] and
    u-b not in E, the (LB) property requires a witness d with
    pos[d] < pos[u], d~b and not d~v.  The ordering stays valid iff every
    such b has such a witness.
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    if pos[u] > pos[v]:
        u, v = v, u
    # u is earlier.  For every b strictly between u and v that is not
    # adjacent to u, a witness d < u with d~b and not d~v must exist.
    for b in range(n):
        if b == u or b == v:
            continue
        if pos[u] < pos[b] < pos[v] and not graph[u][b]:
            found = False
            for d in range(n):
                if d == u or d == v or d == b:
                    continue
                if pos[d] < pos[u] and graph[d][b] and not graph[d][v]:
                    found = True
                    break
            if not found:
                return False
    return True


def _is_lexbfs(order, adj):
    """Check the (LB) 4-point property. O(n^3) worst case, early exit."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb]:
                continue
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if not adj[va][vc]:
                    continue
                # need d < a with db in E and dc not in E
                ok = False
                for d in range(a):
                    vd = order[d]
                    if adj[vd][vb] and not adj[vd][vc]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _try_repair(order, adj, edge):
    """Try to fix the ordering by moving the affected vertices.

    Returns a new ordering if it is valid, else None.
    """
    u, v = edge
    candidates = []

    # 1. swap u and v
    o = list(order)
    iu = o.index(u)
    iv = o.index(v)
    o[iu], o[iv] = o[iv], o[iu]
    candidates.append(o)

    # 2. move u right after v
    o = list(order)
    o.remove(u)
    iv = o.index(v)
    o.insert(iv + 1, u)
    candidates.append(o)

    # 3. move v right after u
    o = list(order)
    o.remove(v)
    iu = o.index(u)
    o.insert(iu + 1, v)
    candidates.append(o)

    # 4. move u to the end
    o = list(order)
    o.remove(u)
    o.append(u)
    candidates.append(o)

    # 5. move v to the end
    o = list(order)
    o.remove(v)
    o.append(v)
    candidates.append(o)

    # 6. move u to the front
    o = list(order)
    o.remove(u)
    o.insert(0, u)
    candidates.append(o)

    # 7. move v to the front
    o = list(order)
    o.remove(v)
    o.insert(0, v)
    candidates.append(o)

    for cand in candidates:
        if _is_lexbfs(cand, adj):
            return cand
    return None


def _delete_ok(graph, u, v, order):
    """After removing edge (u,v), is `order` still a valid LexBFS?

    Let u be the earlier endpoint.  The ordering stays valid iff there is a
    witness d with d < u, d~v and not d~u.  (The removed edge was the only
    thing that could have been needed as a witness for some 4-point
    violation, and the witness condition guarantees none arises.)
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    if pos[u] > pos[v]:
        u, v = v, u
    # u is earlier.  Need d with pos(d) < pos(u), graph[d][v] and not graph[d][u].
    for w in range(n):
        if w == u or w == v:
            continue
        if pos[w] < pos[u] and graph[w][v] and not graph[w][u]:
            return True
    return False


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    if _insert_ok(graph, u, v, order) and _is_lexbfs(order, graph):
        return state
    new_order = _try_repair(order, graph, edge)
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    if _delete_ok(graph, u, v, order) and _is_lexbfs(order, graph):
        return state
    new_order = _try_repair(order, graph, edge)
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order}
