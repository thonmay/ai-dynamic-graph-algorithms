"""Dynamic LexBFS ordering (undirected).

Strategy: maintain a valid LexBFS ordering. On each update, try to repair
the existing ordering with a local fix; if that fails, recompute from
scratch with the standard partition-refinement LexBFS (O(n+m)).

Repair idea:
- Insertion (u,v): check the (LB) 4-point property on the new graph.
  If it holds, keep the ordering. Otherwise recompute.
- Deletion (u,v): removing an edge can invalidate the (LB) property
  (a witness d may have relied on the deleted edge), so verify the
  property and recompute if it fails.

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Standard partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # adj: for each vertex, set of neighbors
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    ordered = []
    remaining = set(range(n))
    # label[v] = list of 0/1 for each ordered vertex (in order),
    # 0 if adjacent (neighbors sort first), 1 if not adjacent.
    labels = {v: [] for v in range(n)}

    for _ in range(n):
        # Find the vertex in remaining with lexicographically smallest label
        best = None
        best_label = None
        for v in sorted(remaining):
            if best is None or labels[v] < best_label:
                best = v
                best_label = labels[v]
        ordered.append(best)
        remaining.discard(best)
        # Update labels of remaining vertices
        for v in remaining:
            labels[v].append(0 if best in adj[v] else 1)

    return ordered


def _check_lb_full(graph, ordering):
    """Check the (LB) 4-point property. Returns True if ordering is valid LexBFS."""
    n = len(ordering)
    if n <= 2:
        return True

    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if graph[a][b]:
                continue  # ab in E, no constraint from this pair
            # ab not in E. Now for all c > b with ac in E:
            for k in range(j + 1, n):
                c = ordering[k]
                if not graph[a][c]:
                    continue  # ac not in E, no constraint
                # ac in E, ab not in E, a < b < c.
                # Need: exists d < a (position < i) with db in E and dc not in E.
                found = False
                for l in range(i):
                    d = ordering[l]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_repair_insert(graph, ordering, u, v):
    """Try to repair ordering after inserting edge (u, v).
    Returns a valid ordering or None if repair fails.

    Inserting (u,v) can only create new (LB) violations where the new edge
    plays the role of ac (the "in E" pair).  For a < b < c with ac = (u,v)
    in E and ab not in E, a witness d < a must satisfy db in E and dc not
    in E.  The new edge can only *help* such a witness (it can add db or
    dc edges), so the only dangerous case is when the new edge is ac and
    the witness d is one of u or v.  We check exactly that.
    """
    n = len(ordering)
    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    pu, pv = pos[u], pos[v]

    if pu < pv:
        # a = u, c = v
        # For all b with pu < pos(b) < pv and graph[u][b] == 0:
        #   need exists d with pos(d) < pu and graph[d][b] and not graph[d][v]
        for b in ordering[pu + 1:pv]:
            if graph[u][b]:
                continue
            found = False
            for d in ordering[:pu]:
                if graph[d][b] and not graph[d][v]:
                    found = True
                    break
            if not found:
                return None
    else:
        # a = v, c = u
        for b in ordering[pv + 1:pu]:
            if graph[v][b]:
                continue
            found = False
            for d in ordering[:pv]:
                if graph[d][b] and not graph[d][u]:
                    found = True
                    break
            if not found:
                return None

    return ordering  # still valid


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    repaired = _try_repair_insert(graph, ordering, u, v)
    if repaired is not None:
        state['ordering'] = repaired
        return state
    # Fallback: recompute
    state['ordering'] = _lexbfs(graph)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    # Deletion can invalidate the (LB) property: a witness d for some
    # triple may have relied on the deleted edge (d,b). Verify and
    # recompute if the ordering is no longer valid.
    ordering = state['ordering']
    if not _check_lb_full(graph, ordering):
        state['ordering'] = _lexbfs(graph)
    return state
