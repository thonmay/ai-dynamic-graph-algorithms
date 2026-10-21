"""Dynamic LexBFS ordering (candidate gen002_c04).

Maintains a valid LexBFS ordering under edge insertions and deletions.

- init: run the static LexBFS (label-based, O(n^3) worst case).
- insert_edge: try a cheap local certification; if it fails, recompute.
- delete_edge: try a cheap local certification; if it fails, recompute.

Local certification for insertion of (u,v):
  Assume p(u) < p(v).  The new edge can only break the (LB) 4-point property
  for triples (a=u, b, c=v) where p(u) < p(b) < p(v) and ub not in E.
  For each such b we need a witness d < p(u) with db in E and dv not in E.
  If all such b have a witness, the ordering stays valid.

Local certification for deletion of (u,v):
  The deleted edge can break the property in two ways:
    (a) as a witness edge db: for each triple (a, b, c) with a < b < c,
        ac in E, ab not in E, where {d, b} = {u,v}, we need another witness.
    (b) as the ab edge: deleting (u,v) makes ab not in E for triples
        (a=u, b=v, c) or (a=v, b=u, c) with c after both, which newly
        require a witness d < a with db in E and dc not in E.
  We check all such triples; if all have a witness, the ordering stays valid.
"""


def _lexbfs(graph):
    """Static LexBFS.  Returns a list of all n vertices in LexBFS order."""
    n = len(graph)
    if n == 0:
        return []

    ordering = []
    remaining = set(range(n))
    labels = {v: frozenset() for v in range(n)}

    while remaining:
        best = None
        best_label = None
        for v in sorted(remaining):
            lv = labels[v]
            if best is None:
                best = v
                best_label = lv
            else:
                if lv != best_label:
                    tl = sorted(lv)
                    tb = sorted(best_label)
                    if tl > tb:
                        best = v
                        best_label = lv
                else:
                    if v < best:
                        best = v
                        best_label = lv
        ordering.append(best)
        remaining.remove(best)
        for v in remaining:
            if graph[v][best]:
                labels[v] = labels[v] | frozenset([best])

    return ordering


def _certify_insert(graph, edge, ordering):
    """Certify that ordering is still valid after inserting edge.

    The new edge (u,v) can only break the property as the ac edge of a
    triple (a=u, b, c=v) or (a=v, b, c=u) with a < b < c and ab not in E.
    For each such b we need a witness d < a with db in E and dc not in E.

    Returns True if valid, False if recompute is needed.
    """
    u, v = edge
    n = len(ordering)
    pos = {vertex: i for i, vertex in enumerate(ordering)}
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu

    for idx in range(pu + 1, pv):
        b = ordering[idx]
        if graph[u][b]:
            continue
        found = False
        for d_idx in range(pu):
            d = ordering[d_idx]
            if graph[d][b] and not graph[d][v]:
                found = True
                break
        if not found:
            return False
    return True


def _certify_delete(graph, edge, ordering):
    """Certify that ordering is still valid after deleting edge.

    The deleted edge (u,v) can break the property in two ways:
      (a) as a witness edge db: for each triple (a, b, c) with a < b < c,
          ac in E, ab not in E, where {d, b} = {u, v} for some d < a, we
          need another witness.
      (b) as the ab edge: deleting (u,v) makes ab not in E for triples
          (a=u, b=v, c) or (a=v, b=u, c) with c after both, which newly
          require a witness d < a with db in E and dc not in E.

    Returns True if valid, False if recompute is needed.
    """
    u, v = edge
    n = len(ordering)
    pos = {vertex: i for i, vertex in enumerate(ordering)}
    pu = pos[u]
    pv = pos[v]

    # Case 3a: deleted edge is the ab edge, a = u, b = v (pu < pv).
    # For each c with pos(c) > pv: if uc in E, then after deletion
    # ab not in E, so we need a witness d < pu with dv in E and dc not in E.
    for c_idx in range(pv + 1, n):
        c = ordering[c_idx]
        if not graph[u][c]:
            continue
        found = False
        for d_idx in range(pu):
            d = ordering[d_idx]
            if graph[d][v] and not graph[d][c]:
                found = True
                break
        if not found:
            return False

    # Case 3b: deleted edge is the ab edge, a = v, b = u (pv < pu).
    # For each c with pos(c) > pu: if vc in E, then after deletion
    # ab not in E, so we need a witness d < pv with du in E and dc not in E.
    for c_idx in range(pu + 1, n):
        c = ordering[c_idx]
        if not graph[v][c]:
            continue
        found = False
        for d_idx in range(pv):
            d = ordering[d_idx]
            if graph[d][u] and not graph[d][c]:
                found = True
                break
        if not found:
            return False

    # Case 1: d = u, b = v.  u < a < v (positions).
    # For each a with pu < pos(a) < pv, and each c with pos(a) < pos(c):
    #   if ac in E and av not in E: need witness d' < a, d' != u,
    #   with d'v in E and d'c not in E.
    for a_idx in range(pu + 1, pv):
        a = ordering[a_idx]
        if graph[a][v]:
            continue
        for c_idx in range(a_idx + 1, n):
            c = ordering[c_idx]
            if not graph[a][c]:
                continue
            found = False
            for d_idx in range(a_idx):
                d = ordering[d_idx]
                if d == u:
                    continue
                if graph[d][v] and not graph[d][c]:
                    found = True
                    break
            if not found:
                return False

    # Case 2: d = v, b = u.  v < a < u (positions).
    # For each a with pv < pos(a) < pu, and each c with pos(a) < pos(c):
    #   if ac in E and au not in E: need witness d' < a, d' != v,
    #   with d'u in E and d'c not in E.
    for a_idx in range(pv + 1, pu):
        a = ordering[a_idx]
        if graph[a][u]:
            continue
        for c_idx in range(a_idx + 1, n):
            c = ordering[c_idx]
            if not graph[a][c]:
                continue
            found = False
            for d_idx in range(a_idx):
                d = ordering[d_idx]
                if d == v:
                    continue
                if graph[d][u] and not graph[d][c]:
                    found = True
                    break
            if not found:
                return False

    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _certify_insert(graph, edge, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': state['n']}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _certify_delete(graph, edge, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': state['n']}
