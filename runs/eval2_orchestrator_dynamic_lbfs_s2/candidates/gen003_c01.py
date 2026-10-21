"""Dynamic LexBFS ordering (candidate gen003_c01).

Maintains a valid LexBFS ordering under edge insertions and deletions.

- init: run the static LexBFS (label-based, O(n^3) worst case).
- insert_edge: try a local certification over all triple families whose
  status can change when the edge is added; if it fails, recompute.
- delete_edge: try a local certification over all triple families whose
  status can change when the edge is removed; if it fails, recompute.

Validity is the (LB) 4-point property of Corneil and Krueger: for all
positions a < b < c with ac in E and ab not in E, there exists d < a with
db in E and dc not in E.  The witness edges always go to b and c.
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


def _witness_exists(graph, ordering, a_idx, b, c, exclude=()):
    """True iff some d < a (d not in exclude) has db in E and dc not in E."""
    for d_idx in range(a_idx):
        d = ordering[d_idx]
        if d in exclude:
            continue
        if graph[d][b] and not graph[d][c]:
            return True
    return False


def _certify_insert(graph, edge, ordering):
    """Certify that ordering is still valid after inserting edge (u,v).

    The new edge can change the status of a triple (a, b, c) with
    a < b < c in three ways:

    Family A (new edge = ac): (a=u, b, c=v) and (a=v, b, c=u) for b
      strictly between a and c in position, with ab not in E.
    Family B (new edge = ab): (a=u, b=v, c) and (a=v, b=u, c) for c
      after both, with ac in E.
    Family C (new edge = dc): (a, b=u, c=v) and (a, b=v, c=u) for a
      before both, with ac in E and ab not in E.

    For every such triple a witness d < a with db in E and dc not in E
    must exist (in family C, d may not be the other endpoint of the new
    edge, since dc is the new edge and hence in E).  If any triple lacks
    a witness, return False so the caller recomputes.
    """
    u, v = edge
    n = len(ordering)
    pos = {vertex: i for i, vertex in enumerate(ordering)}
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu

    # Family A: new edge is ac.  a = u, c = v, b strictly between.
    for b_idx in range(pu + 1, pv):
        b = ordering[b_idx]
        if graph[u][b]:
            continue
        if not _witness_exists(graph, ordering, pu, b, v):
            return False

    # Family B: new edge is ab.  a = u, b = v, c after both.
    for c_idx in range(pv + 1, n):
        c = ordering[c_idx]
        if not graph[u][c]:
            continue
        if not _witness_exists(graph, ordering, pu, v, c):
            return False

    # Family C: new edge is dc.  a before both, b = u, c = v.
    for a_idx in range(pu):
        a = ordering[a_idx]
        if not graph[a][v]:
            continue
        if graph[a][u]:
            continue
        if not _witness_exists(graph, ordering, a_idx, u, v, exclude=(v,)):
            return False

    return True


def _certify_delete(graph, edge, ordering):
    """Certify that ordering is still valid after deleting edge (u,v).

    The deleted edge can change the status of a triple (a, b, c) with
    a < b < c in three ways:

    Family A (deleted edge = ac): (a=u, b, c=v) and (a=v, b, c=u) for b
      strictly between a and c in position, with ab not in E.  These
      triples no longer have an obligation.
    Family B (deleted edge = ab): (a=u, b=v, c) and (a=v, b=u, c) for c
      after both, with ac in E.  These triples newly require a witness
      d < a with db in E and dc not in E.
    Family C (deleted edge = dc): (a, b=u, c=v) and (a, b=v, c=u) for a
      before both, with ac in E and ab not in E.  The deleted edge may
      have been the witness edge db; each such triple needs another
      witness d' < a, d' != the deleted endpoint, with d'b in E and
      d'c not in E.

    If any newly obligated or de-witnessed triple lacks a witness,
    return False so the caller recomputes.
    """
    u, v = edge
    n = len(ordering)
    pos = {vertex: i for i, vertex in enumerate(ordering)}
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu

    # Family B: deleted edge is ab.  a = u, b = v, c after both.
    for c_idx in range(pv + 1, n):
        c = ordering[c_idx]
        if not graph[u][c]:
            continue
        if not _witness_exists(graph, ordering, pu, v, c):
            return False

    # Family C: deleted edge is dc.  a before both, b = u, c = v.
    for a_idx in range(pu):
        a = ordering[a_idx]
        if not graph[a][v]:
            continue
        if graph[a][u]:
            continue
        if not _witness_exists(graph, ordering, a_idx, u, v, exclude=(v,)):
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
