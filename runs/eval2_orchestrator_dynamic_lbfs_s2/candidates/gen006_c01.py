"""Dynamic LexBFS ordering (candidate gen006_c01).

Maintains a valid LexBFS ordering under edge insertions and deletions.

- init: run the static LexBFS (label-based, O(n^3) worst case).
- insert_edge / delete_edge: try a cheap local certification; if it fails,
  recompute.

The (LB) 4-point property (Corneil and Krueger): for all positions
a < b < c with ac in E and ab not in E, there exists d < a with db in E and dc not in E.

Local certification for insertion of (u,v), assume pu < pv:
  The new edge can break the property in two ways:
    Case A (ac edge): triple (a=u, b, c=v) with pu < pos(b) < pv and ub not in E.
      For each such b we need a witness d < pu with db in E and dv not in E.
    Case B (ab edge): triple (a=u, b=v, c) with pos(c) > pv and uc in E.
      Before insertion (u,v) was not in E so no witness was required; after
      insertion (u,v) is in E, so we need a witness d < pu with dv in E and
      dc not in E.
  The new edge as the witness edge db can only ADD witnesses, never remove
  them, so it cannot create a violation.

Local certification for deletion of (u,v), assume pu < pv:
  The deleted edge can break the property in three ways:
    Case 1 (ab edge): triple (a=u, b=v, c) with pos(c) > pv and uc in E.
      Before deletion ab was in E so no witness was required; after
      deletion ab not in E, so we need a witness d < pu with dv in E and
      dc not in E.
    Case 2 (ac edge): triple (a, b, c=v) with pu < pos(a) < pos(b) < pv,
      av in E and ab not in E.  The ac edge is gone, so the triple is no
      longer required to have a witness; this case can never create a
      violation and is checked only for completeness (it always passes).
    Case 3 (witness edge db): triple (a, b, c) with pu < pos(a) < pv,
      av not in E, ac in E, and the only witness d < a was u (i.e. uv in E
      and no other d' < a with d'v in E and d'c not in E).
  The symmetric cases with u and v swapped are handled by swapping.
"""


def _lexbfs(graph):
    """Static LexBFS.  Returns a list of all n vertices in LexBFS order.

    Labels are bit-vectors indexed by output position: after k vertices have
    been output, labels[v][i] is 1 iff v is adjacent to the vertex output at
    position i.  Labels are compared lexicographically in output order
    (earlier positions more significant), which is the LexBFS rule.
    """
    n = len(graph)
    if n == 0:
        return []

    ordering = []
    remaining = set(range(n))
    labels = {v: [] for v in range(n)}

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
                    if tuple(lv) > tuple(best_label):
                        best = v
                        best_label = lv
                else:
                    if v < best:
                        best = v
                        best_label = lv
        ordering.append(best)
        remaining.remove(best)
        for v in remaining:
            labels[v].append(1 if graph[v][best] else 0)

    return ordering


def _certify_insert(graph, edge, ordering):
    """Certify that ordering is still valid after inserting edge.

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

    # Case A (ac edge): triple (a=u, b, c=v) with pu < pos(b) < pv and
    # ub not in E.  A witness d < pu with db in E and dv not in E is
    # required.
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

    # Case B (ab edge): triple (a=u, b=v, c) with pos(c) > pv and uc in E.
    # After insertion (u,v) is in E, so a witness d < pu with dv in E and
    # dc not in E is required.
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

    return True


def _certify_delete(graph, edge, ordering):
    """Certify that ordering is still valid after deleting edge.

    The graph passed in is the graph AFTER the deletion.  The deleted edge
    (u,v) can break the (LB) property in three ways: as the ab edge of a
    triple (activating a new witness obligation), as the ac edge (removing
    an obligation, never a violation), or as the witness edge db (removing
    a witness).  All three are checked.

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

    # Case 1 (ab edge): triple (a=u, b=v, c) with pos(c) > pv and uc in E.
    # After deletion ab not in E, so a witness d < pu with dv in E and
    # dc not in E is required.
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

    # Case 2 (ac edge): triple (a, b, c=v) with pu < pos(a) < pos(b) < pv,
    # av in E and ab not in E.  The ac edge is gone, so the obligation is
    # removed; this case can never create a violation.  No check needed.

    # Case 3 (witness edge db): triple (a, b, c) with pu < pos(a) < pv,
    # av not in E, ac in E, and the only witness d < a was u (uv in E).
    # After deletion, no witness may remain.
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
