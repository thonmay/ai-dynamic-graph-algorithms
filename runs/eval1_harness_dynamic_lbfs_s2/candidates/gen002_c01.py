"""Dynamic algorithm candidate. Edit this file; keep the three functions.

Strategy: keep the old LexBFS ordering after an update when it is still valid,
and only recompute from scratch when a single edge flip actually breaks the
(LB) 4-point property. After flipping edge (u, v), only triples (a, b, c) with
at least one of a, b, c in {u, v} can change (LB) status (the flip touches
only edges incident to u or v, and for triples with a, b, c all outside
{u, v} neither the antecedent nor any witness edge changes). So validity is
certified by checking exactly those affected triples, in O(n^2), using a
maintained minD[b][c] = earliest (in the ordering) vertex d that is a
neighbour of b and a non-neighbour of c. minD changes only for pairs with b
or c in {u, v}, so it is updated incrementally in O(n^2) per flip.
"""

INF = 10 ** 9


def _lexbfs(graph):
    """Partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

    Starts at vertex 0 with the minimum-id tie-break. Returns a valid
    LexBFS ordering of the undirected graph given as a 0/1 adjacency matrix.
    """
    n = len(graph)
    Pi = [list(range(n))]
    order = []
    for _ in range(n):
        p = Pi[0][0]
        order.append(p)
        if len(Pi[0]) == 1:
            Pi = Pi[1:]
        else:
            Pi[0] = Pi[0][1:]
        row = graph[p]
        newPi = []
        for C in Pi:
            a = [v for v in C if row[v]]
            b = [v for v in C if not row[v]]
            if a:
                newPi.append(a)
            if b:
                newPi.append(b)
        Pi = newPi
    return order


def _mind_pair(graph, pos, n, b, c):
    """Earliest (in `pos`) vertex d that is a neighbour of b and a
    non-neighbour of c, or INF if none. This is the witness for the (LB)
    consequent of any triple whose later two vertices are (b, c)."""
    if b == c:
        return INF
    best = INF
    for d in range(n):
        if d != b and d != c and graph[b][d] and not graph[c][d]:
            pd = pos[d]
            if pd < best:
                best = pd
    return best


def _mind_all(graph, pos, n):
    return [[_mind_pair(graph, pos, n, b, c) for c in range(n)] for b in range(n)]


def _pos_of(ordering):
    pos = [0] * len(ordering)
    for i, v in enumerate(ordering):
        pos[v] = i
    return pos


def _focused_valid(graph, pos, minD, n, u, v):
    """Check (LB) for every triple (a, b, c) with pos a < b < c and at least
    one of a, b, c in {u, v}. Triples with all three outside {u, v} are
    unaffected by the flip, so they need not be checked."""
    for a in (u, v):
        pa = pos[a]
        for b in range(n):
            if b == a:
                continue
            pb = pos[b]
            if pb <= pa:
                continue
            gab = graph[a][b]
            for c in range(n):
                if c == a or c == b:
                    continue
                pc = pos[c]
                if pc <= pb:
                    continue
                if graph[a][c] and not gab:
                    if minD[b][c] >= pa:
                        return False
    for b in (u, v):
        pb = pos[b]
        for a in range(n):
            if a == b:
                continue
            pa = pos[a]
            if pa >= pb:
                continue
            gab = graph[a][b]
            for c in range(n):
                if c == a or c == b:
                    continue
                pc = pos[c]
                if pc <= pb:
                    continue
                if graph[a][c] and not gab:
                    if minD[b][c] >= pa:
                        return False
    for c in (u, v):
        pc = pos[c]
        for a in range(n):
            if a == c:
                continue
            pa = pos[a]
            for b in range(n):
                if b == a or b == c:
                    continue
                pb = pos[b]
                if pb <= pa or pb >= pc:
                    continue
                if graph[a][c] and not graph[a][b]:
                    if minD[b][c] >= pa:
                        return False
    return True


def _rebuild(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    pos = _pos_of(ordering)
    minD = _mind_all(graph, pos, n)
    return {"ordering": ordering, "pos": pos, "minD": minD, "n": n}


def init(graph):
    return _rebuild(graph)


def _update(graph, edge, state):
    n = state["n"]
    u, v = edge
    pos = state["pos"]
    minD = [row[:] for row in state["minD"]]
    # Only pairs with b or c in {u, v} change; recompute those.
    for b in (u, v):
        for c in range(n):
            if c != b:
                minD[b][c] = _mind_pair(graph, pos, n, b, c)
    for c in (u, v):
        for b in range(n):
            if b != c:
                minD[b][c] = _mind_pair(graph, pos, n, b, c)
    if _focused_valid(graph, pos, minD, n, u, v):
        return {"ordering": state["ordering"], "pos": pos, "minD": minD, "n": n}
    return _rebuild(graph)


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)
