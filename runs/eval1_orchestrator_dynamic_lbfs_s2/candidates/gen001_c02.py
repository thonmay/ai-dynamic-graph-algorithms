"""Dynamic LexBFS ordering.

Strategy: maintain a LexBFS ordering incrementally.

- init: static partition-refinement LexBFS, O(n^2).
- insert_edge: check if the new edge creates a 4-point violation.
  If not, keep the ordering; otherwise recompute.
- delete_edge: check if the removed edge was a unique witness for some
  4-point condition, or if the new non-edge creates a new violation.
  If not, keep the ordering; otherwise recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement.  Returns the ordering."""
    n = len(graph)
    if n == 0:
        return []

    # Partition: list of lists of unprocessed vertices.
    part = [list(range(n))]
    ordering = []

    for _ in range(n):
        # Find the first non-empty bucket.
        bi = None
        for i, b in enumerate(part):
            if b:
                bi = i
                break
        if bi is None:
            break

        # Take the first vertex in this bucket.
        v = part[bi][0]
        part[bi] = part[bi][1:]
        ordering.append(v)

        # Refine the partition by N(v): for each bucket, split into
        # (intersection with N(v), rest).  The intersection part goes
        # before the rest.
        new_part = []
        for b in part:
            if not b:
                continue
            inter = [x for x in b if graph[v][x]]
            rest = [x for x in b if not graph[v][x]]
            if inter:
                new_part.append(inter)
            if rest:
                new_part.append(rest)
        part = new_part

    return ordering


def _recompute(graph):
    """Recompute the LexBFS ordering from scratch."""
    return _lexbfs(graph)


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle edge insertion.  Check if the ordering is still valid.

    Adding edge (u,v) can only create new violations where the new edge
    is the "ac" edge (making ac in E where it was previously not).
    It cannot create new non-edges, so it cannot create new "ab not in E"
    or "dc not in E" conditions.
    """
    u, v = edge
    ordering = state['ordering']
    n = len(ordering)

    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    pu = pos[u]
    pv = pos[v]

    # Case 1: a = u, c = v (pu < pv)
    # For all b with pu < pos[b] < pv and graph[u][b] == 0:
    #   need exists d < pu with graph[d][b] == 1 and graph[d][v] == 0
    if pu < pv:
        for b in range(pu + 1, pv):
            vb = ordering[b]
            if graph[u][vb]:
                continue  # ab in E, condition not triggered
            found = False
            for d in range(pu):
                vd = ordering[d]
                if graph[vd][vb] and not graph[vd][v]:
                    found = True
                    break
            if not found:
                return {'ordering': _recompute(graph)}

    # Case 2: a = v, c = u (pv < pu)
    # For all b with pv < pos[b] < pu and graph[v][b] == 0:
    #   need exists d < pv with graph[d][b] == 1 and graph[d][u] == 0
    if pv < pu:
        for b in range(pv + 1, pu):
            vb = ordering[b]
            if graph[v][vb]:
                continue  # ab in E, condition not triggered
            found = False
            for d in range(pv):
                vd = ordering[d]
                if graph[vd][vb] and not graph[vd][u]:
                    found = True
                    break
            if not found:
                return {'ordering': _recompute(graph)}

    return state


def delete_edge(graph, edge, state):
    """Handle edge deletion.  Check if the ordering is still valid.

    Removing edge (u,v) can:
    1. Create new "ab not in E" conditions where {a,b} = {u,v}.
    2. Remove "db in E" witnesses where {d,b} = {u,v}.
    It cannot create new "ac in E" conditions (removing an edge only
    removes edges), and it can only help with "dc not in E" conditions.
    """
    u, v = edge
    ordering = state['ordering']
    n = len(ordering)

    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    pu = pos[u]
    pv = pos[v]

    # Case 1a: a = u, b = v (pu < pv)
    # For all c > pv with graph[u][c] == 1:
    #   need exists d < pu with graph[d][v] == 1 and graph[d][c] == 0
    if pu < pv:
        for c in range(pv + 1, n):
            vc = ordering[c]
            if not graph[u][vc]:
                continue  # ac not in E
            found = False
            for d in range(pu):
                vd = ordering[d]
                if graph[vd][v] and not graph[vd][vc]:
                    found = True
                    break
            if not found:
                return {'ordering': _recompute(graph)}

    # Case 1b: a = v, b = u (pv < pu)
    # For all c > pu with graph[v][c] == 1:
    #   need exists d < pv with graph[d][u] == 1 and graph[d][c] == 0
    if pv < pu:
        for c in range(pu + 1, n):
            vc = ordering[c]
            if not graph[v][vc]:
                continue  # ac not in E
            found = False
            for d in range(pv):
                vd = ordering[d]
                if graph[vd][u] and not graph[vd][vc]:
                    found = True
                    break
            if not found:
                return {'ordering': _recompute(graph)}

    # Case 2a: d = u, b = v (pu < pv)
    # For all a with pu < pos[a] < pv, all c > pos[a] with
    # graph[a][c] == 1 and graph[a][v] == 0:
    #   need exists d' < a, d' != u, with graph[d'][v] == 1 and graph[d'][c] == 0
    if pu < pv:
        for a in range(pu + 1, pv):
            va = ordering[a]
            if graph[va][v]:
                continue  # ab in E, condition not triggered
            for c in range(a + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue  # ac not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if vd == u:
                        continue  # this witness is gone
                    if graph[vd][v] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return {'ordering': _recompute(graph)}

    # Case 2b: d = v, b = u (pv < pu)
    # For all a with pv < pos[a] < pu, all c > pos[a] with
    # graph[a][c] == 1 and graph[a][u] == 0:
    #   need exists d' < a, d' != v, with graph[d'][u] == 1 and graph[d'][c] == 0
    if pv < pu:
        for a in range(pv + 1, pu):
            va = ordering[a]
            if graph[va][u]:
                continue  # ab in E, condition not triggered
            for c in range(a + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue  # ac not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if vd == v:
                        continue  # this witness is gone
                    if graph[vd][u] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return {'ordering': _recompute(graph)}

    return state
