"""Dynamic LexBFS ordering (undirected).

Strategy: maintain a valid LexBFS ordering. On each update, verify the
(LB) 4-point property on the new graph; if it fails, recompute from
scratch with the standard partition-refinement LexBFS (O(n+m)).

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.

Optimization: the check is restricted to triples where at least one of the
four edges (ac, ab, db, dc) is the updated edge (x, y). This is O(n) per
update instead of O(n^4).
"""


def _lexbfs(graph):
    """Standard partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    ordered = []
    remaining = set(range(n))
    labels = {v: [] for v in range(n)}

    for _ in range(n):
        best = None
        best_label = None
        for v in sorted(remaining):
            if best is None or labels[v] < best_label:
                best = v
                best_label = labels[v]
        ordered.append(best)
        remaining.discard(best)
        for v in remaining:
            labels[v].append(0 if best in adj[v] else 1)

    return ordered


def _check_lb_affected(graph, ordering, pos, x, y):
    """Check the (LB) 4-point property restricted to triples involving
    the updated edge (x, y).

    Returns True if the ordering is still a valid LexBFS ordering.
    """
    n = len(ordering)
    px, py = pos[x], pos[y]
    if px > py:
        px, py = py, px

    # The updated edge (x, y) can only affect triples where at least one
    # of the four edges (ac, ab, db, dc) is (x, y).
    #
    # We enumerate all such triples and check the (LB) condition.

    # Case A: a = x (pos[a] = px).
    #   b, c with px < pos[b] < pos[c].
    #   ac in E, ab not in E.
    #   Witness: d < a with db in E and dc not in E.
    #   Updated edge (x, y) appears in:
    #     - ac when c = y
    #     - ab when b = y
    #   So we need: b = y or c = y.

    # A1: a = x, b = y.
    #   px < py < pos[c].
    #   ac = (x, c) in E, ab = (x, y) not in E.
    #   Witness: d < x with (d, y) in E and (d, c) not in E.
    if not graph[x][y]:
        for c in ordering:
            pc = pos[c]
            if pc <= py:
                continue
            if not graph[x][c]:
                continue
            found = False
            for d in ordering:
                pd = pos[d]
                if pd >= px:
                    break
                if graph[d][y] and not graph[d][c]:
                    found = True
                    break
            if not found:
                return False

    # A2: a = x, c = y.
    #   px < pos[b] < py.
    #   ac = (x, y) in E, ab = (x, b) not in E.
    #   Witness: d < x with (d, b) in E and (d, y) not in E.
    if graph[x][y]:
        for b in ordering:
            pb = pos[b]
            if pb <= px or pb >= py:
                continue
            if graph[x][b]:
                continue
            found = False
            for d in ordering:
                pd = pos[d]
                if pd >= px:
                    break
                if graph[d][b] and not graph[d][y]:
                    found = True
                    break
            if not found:
                return False

    # Case B: a = y (pos[a] = py).
    #   b, c with py < pos[b] < pos[c].
    #   Updated edge (x, y) appears in:
    #     - ac when c = x (impossible since pos[c] > py > px)
    #     - ab when b = x (impossible since pos[b] > py > px)
    #   So no triples with a = y are affected.

    # Case C: b = x (pos[b] = px).
    #   a, c with pos[a] < px < pos[c].
    #   ac in E, ab = (a, x) not in E.
    #   Witness: d < a with (d, x) in E and (d, c) not in E.
    #   Updated edge (x, y) appears in:
    #     - ac when c = y
    #     - ab when a = y (impossible since pos[a] < px < py)
    #     - db when d = y
    #     - dc when c = y
    #   So we need: c = y or d = y.

    # C1: b = x, c = y.
    #   pos[a] < px < py.
    #   ac = (a, y) in E, ab = (a, x) not in E.
    #   Witness: d < a with (d, x) in E and (d, y) not in E.
    for a in ordering:
        pa = pos[a]
        if pa >= px:
            continue
        if not graph[a][y]:
            continue
        if graph[a][x]:
            continue
        found = False
        for d in ordering:
            pd = pos[d]
            if pd >= pa:
                break
            if graph[d][x] and not graph[d][y]:
                found = True
                break
        if not found:
            return False

    # C2: b = x, d = y (witness is y).
    #   pos[a] < px, pos[c] > px.
    #   ac in E, ab = (a, x) not in E.
    #   Witness: d = y < a with (y, x) in E and (y, c) not in E.
    #   So py < pa < px. But px < py, so this is impossible.

    # Case D: b = y (pos[b] = py).
    #   a, c with pos[a] < py < pos[c].
    #   ac in E, ab = (a, y) not in E.
    #   Witness: d < a with (d, y) in E and (d, c) not in E.
    #   Updated edge (x, y) appears in:
    #     - ac when c = x (impossible since pos[c] > py > px)
    #     - ab when a = x
    #     - db when d = x
    #     - dc when c = x (impossible)
    #   So we need: a = x or d = x.

    # D1: b = y, a = x.
    #   px < py < pos[c].
    #   ac = (x, c) in E, ab = (x, y) not in E.
    #   Witness: d < x with (d, y) in E and (d, c) not in E.
    #   This is the same as A1, already checked.

    # D2: b = y, d = x (witness is x).
    #   pos[a] < py, pos[c] > py.
    #   ac in E, ab = (a, y) not in E.
    #   Witness: d = x < a with (x, y) in E and (x, c) not in E.
    #   So px < pa < py.
    #   The updated edge affects db = (x, y) and dc = (x, c).
    #   If (x, y) is not in E, x is not a witness.
    #   If (x, y) is in E, x is a witness iff (x, c) is not in E.
    #   We need to check if there EXISTS a witness. If x is a witness, we're done.
    #   If x is not a witness, there might be another d.
    #   So we only need to check if x is NOT a witness AND no other d is a witness.
    #   This is the same as the full check for this triple.
    if graph[x][y]:
        for a in ordering:
            pa = pos[a]
            if pa <= px or pa >= py:
                continue
            if graph[a][y]:
                continue  # ab in E, no constraint
            for c in ordering:
                pc = pos[c]
                if pc <= py:
                    continue
                if not graph[a][c]:
                    continue  # need ac in E
                # Check if x is a witness: (x, y) in E (true) and (x, c) not in E.
                if not graph[x][c]:
                    continue  # x is a witness, (LB) satisfied
                # x is not a witness. Check if there's another d < a with
                # (d, y) in E and (d, c) not in E.
                found = False
                for d in ordering:
                    pd = pos[d]
                    if pd >= pa:
                        break
                    if graph[d][y] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False

    return True


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    pos = {v: i for i, v in enumerate(ordering)}
    if not _check_lb_affected(graph, ordering, pos, u, v):
        state['ordering'] = _lexbfs(graph)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    pos = {v: i for i, v in enumerate(ordering)}
    if not _check_lb_affected(graph, ordering, pos, u, v):
        state['ordering'] = _lexbfs(graph)
    return state
