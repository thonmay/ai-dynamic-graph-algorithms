"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via bucket lists.
- insert_edge(u,v): if the current ordering is still valid, keep it.
  Otherwise recompute.
- delete_edge(u,v): if the current ordering is still valid, keep it.
  Otherwise recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

To avoid a full recompute after an update (u, v), we run two filters:

1. A cheap O(n) necessary condition: the (LB) property restricted to the
   updated edge.  If the update is an insertion (u, v) with pos[u] < pos[v],
   then for every a < u with au in E and av not in E, we need a witness
   d < a with du in E and dv not in E.  If the update is a deletion, the
   same condition must hold for every a < u with au in E and av in E
   (the edge av is still present in the new graph).  If this fails, the
   ordering is definitely invalid and we recompute.

2. A full O(n^2) check using a cached min_d_pos table.  The table
   min_d_pos[b][c] = min{ pos[d] : db in E, dc not in E, pos[d] < pos[b] }
   is maintained incrementally: after an update (u, v), only the entries
   min_d_pos[u][c] and min_d_pos[c][u] can change, so we recompute those
   two rows in O(n^2) and then run the full triple check in O(n^2).

If both filters pass, the ordering is kept; otherwise we recompute.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    pos = [-1] * n
    buckets = [[v for v in range(n)]]
    label_id = [0] * n

    ordering = []

    while len(ordering) < n:
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        v = buckets[bi].pop(0)
        pos[v] = len(ordering)
        ordering.append(v)

        new_buckets = []
        for b in buckets:
            if not b:
                new_buckets.append([])
                continue
            nb = [x for x in b if graph[v][x]]
            nnb = [x for x in b if not graph[v][x]]
            if nb:
                new_buckets.append(nb)
                for x in nb:
                    label_id[x] = len(new_buckets) - 1
            if nnb:
                new_buckets.append(nnb)
                for x in nnb:
                    label_id[x] = len(new_buckets) - 1
            if not nb and not nnb:
                new_buckets.append([])
        buckets = new_buckets

    return ordering


def _build_min_d_pos(graph, pos):
    """Build the min_d_pos table.

    min_d_pos[b][c] = min{ pos[d] : db in E, dc not in E, pos[d] < pos[b] }
    or INF if no such d exists.  Only meaningful when pos[b] < pos[c] and
    bc in E; other entries are set to INF.
    """
    n = len(pos)
    INF = n + 1
    table = [[INF] * n for _ in range(n)]
    for b in range(n):
        pb = pos[b]
        for c in range(n):
            if pos[c] <= pb:
                continue
            if not graph[b][c]:
                continue
            best = INF
            for d in range(n):
                if pos[d] >= pb:
                    continue
                if graph[b][d] and not graph[c][d]:
                    if pos[d] < best:
                        best = pos[d]
            table[b][c] = best
    return table


def _update_min_d_pos_row(table, graph, pos, b):
    """Recompute row b of the min_d_pos table in O(n^2)."""
    n = len(pos)
    INF = n + 1
    pb = pos[b]
    row = table[b]
    for c in range(n):
        if pos[c] <= pb:
            row[c] = INF
            continue
        if not graph[b][c]:
            row[c] = INF
            continue
        best = INF
        for d in range(n):
            if pos[d] >= pb:
                continue
            if graph[b][d] and not graph[c][d]:
                if pos[d] < best:
                    best = pos[d]
        row[c] = best


def _cheap_filter(graph, pos, u, v, is_insertion):
    """O(n) necessary condition for the (LB) property after an update (u, v).

    If the update is an insertion (u, v) with pos[u] < pos[v], then for
    every a < u with au in E and av not in E, we need a witness d < a
    with du in E and dv not in E.  If the update is a deletion, the same
    condition must hold for every a < u with au in E and av in E (the
    edge av is still present in the new graph).

    Returns True if the condition holds (ordering might still be valid),
    False if it fails (ordering is definitely invalid).
    """
    n = len(pos)
    pu = pos[u]
    pv = pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu
    # Now pu < pv.  The updated edge is (u, v) with u before v.
    # For every a with pos[a] < pu:
    #   if au in E and av not in E (insertion) or av in E (deletion):
    #     need exists d < a: du in E and dv not in E.
    for a in range(n):
        pa = pos[a]
        if pa >= pu:
            continue
        if not graph[u][a]:
            continue
        # au in E
        if is_insertion:
            # av not in E in the new graph
            if graph[v][a]:
                continue
        else:
            # av in E in the new graph (deletion of (u,v) doesn't affect av)
            if not graph[v][a]:
                continue
        # Need exists d < a: du in E and dv not in E
        found = False
        for d in range(n):
            if pos[d] >= pa:
                continue
            if graph[u][d] and not graph[v][d]:
                found = True
                break
        if not found:
            return False
    return True


def _full_check(graph, pos, table):
    """Full O(n^2) check of the (LB) property using the cached table.

    For all a < b < c with ac in E and ab not in E,
    need min_d_pos[b][c] < pos[a].
    """
    n = len(pos)
    for a in range(n):
        pa = pos[a]
        for b in range(n):
            pb = pos[b]
            if pb <= pa:
                continue
            if graph[a][b]:
                continue
            # ab not in E, pa < pb
            for c in range(n):
                pc = pos[c]
                if pc <= pb:
                    continue
                if not graph[a][c]:
                    continue
                # ac in E, ab not in E, pa < pb < pc
                if table[b][c] >= pa:
                    return False
    return True


def init(graph):
    ordering = _lexbfs(graph)
    n = len(ordering)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    table = _build_min_d_pos(graph, pos)
    return {'ordering': ordering, 'pos': pos, 'min_d_pos': table}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    pos = state['pos']
    table = state['min_d_pos']
    n = len(ordering)

    # Cheap O(n) filter
    if not _cheap_filter(graph, pos, u, v, True):
        ordering = _lexbfs(graph)
        pos = [0] * n
        for i, v2 in enumerate(ordering):
            pos[v2] = i
        table = _build_min_d_pos(graph, pos)
        return {'ordering': ordering, 'pos': pos, 'min_d_pos': table}

    # Update the table: only rows u and v can change
    _update_min_d_pos_row(table, graph, pos, u)
    _update_min_d_pos_row(table, graph, pos, v)

    # Full O(n^2) check
    if _full_check(graph, pos, table):
        return state

    # Recompute
    ordering = _lexbfs(graph)
    pos = [0] * n
    for i, v2 in enumerate(ordering):
        pos[v2] = i
    table = _build_min_d_pos(graph, pos)
    return {'ordering': ordering, 'pos': pos, 'min_d_pos': table}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    pos = state['pos']
    table = state['min_d_pos']
    n = len(ordering)

    # Cheap O(n) filter
    if not _cheap_filter(graph, pos, u, v, False):
        ordering = _lexbfs(graph)
        pos = [0] * n
        for i, v2 in enumerate(ordering):
            pos[v2] = i
        table = _build_min_d_pos(graph, pos)
        return {'ordering': ordering, 'pos': pos, 'min_d_pos': table}

    # Update the table: only rows u and v can change
    _update_min_d_pos_row(table, graph, pos, u)
    _update_min_d_pos_row(table, graph, pos, v)

    # Full O(n^2) check
    if _full_check(graph, pos, table):
        return state

    # Recompute
    ordering = _lexbfs(graph)
    pos = [0] * n
    for i, v2 in enumerate(ordering):
        pos[v2] = i
    table = _build_min_d_pos(graph, pos)
    return {'ordering': ordering, 'pos': pos, 'min_d_pos': table}
