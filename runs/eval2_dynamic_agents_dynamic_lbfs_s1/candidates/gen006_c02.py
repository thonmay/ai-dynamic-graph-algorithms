"""Dynamic LexBFS ordering.

Strategy:
- init: static label-based LexBFS (O(n^2)).
- insert_edge / delete_edge:
    1. Cheap necessary-condition check (O(n)): for each endpoint x of the
       updated edge, the set of neighbors of x must be a prefix of the
       ordering.  If both are prefixes, the ordering is still a valid
       LexBFS and we keep it.
    2. If not, try a cheap local repair: move u or v to a position that
       restores the prefix property, verified by the full 4-point check.
    3. Fall back to a full recompute.

The 4-point (LB) property: for all positions a < b < c with
ordering[a]~ordering[c] and not ordering[a]~ordering[b],
there exists d < a with ordering[d]~ordering[b] and not ordering[d]~ordering[c].
"""


def _lexbfs(graph):
    """Static LexBFS via label-based approach. Returns ordering list."""
    n = len(graph)
    adj = [set() for _ in range(n)]
    for v in range(n):
        for w in range(v + 1, n):
            if graph[v][w]:
                adj[v].add(w)
                adj[w].add(v)

    ordered = []
    remaining = list(range(n))
    labels = {v: [] for v in range(n)}

    for _ in range(n):
        remaining.sort(key=lambda v: labels[v], reverse=True)
        best = remaining[0]
        ordered.append(best)
        remaining.remove(best)
        for v in remaining:
            labels[v].append(1 if best in adj[v] else 0)

    return ordered


def _is_valid_lexbfs(graph, ordering):
    """Check the 4-point (LB) property. Returns True if valid.

    For each position a, precompute the set S of vertices that are
    adjacent to some earlier vertex but not to ordering[a] itself.
    Then for each b > a with a not~ b, the witness d < a exists iff
    ordering[b] is in S.
    """
    n = len(graph)
    for a in range(n):
        va = ordering[a]
        S = set()
        for d in range(a):
            vd = ordering[d]
            if graph[vd][va]:
                continue
            for x in range(n):
                if graph[vd][x]:
                    S.add(x)
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue
            if vb not in S:
                return False
    return True


def _prefix_ok(graph, ordering, pos, x):
    """Necessary condition: neighbors of x form a prefix of the ordering.

    pos[x] = position of vertex x in the ordering.
    Returns True iff for every neighbor y of x, pos[y] < pos[x].
    """
    px = pos[x]
    row = graph[x]
    for y in range(len(row)):
        if row[y] and pos[y] >= px:
            return False
    return True


def _try_local_repair(graph, ordering, u, v):
    """Try to fix the ordering after an edge update involving (u, v).

    Try moving u or v to each position; accept the first candidate that
    passes the full 4-point check.  Returns a valid ordering or None.
    """
    n = len(ordering)

    for x in (u, v):
        for new_pos in range(n):
            candidate = [t for t in ordering if t != x]
            candidate.insert(new_pos, x)
            if _is_valid_lexbfs(graph, candidate):
                return candidate

    return None


def _update(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    n = len(ordering)

    # Cheap necessary-condition check: both endpoints' neighbor sets
    # must be prefixes of the ordering.
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i
    if _prefix_ok(graph, ordering, pos, u) and _prefix_ok(graph, ordering, pos, v):
        return state

    repaired = _try_local_repair(graph, ordering, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    return {'ordering': _lexbfs(graph)}


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)
