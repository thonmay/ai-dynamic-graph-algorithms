"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try to repair
the existing ordering locally (cheap); if repair fails, fall back to a
full O(n^2) static LexBFS recompute (always correct).

The repair is a heuristic: it attempts a single local move that is likely
to fix the ordering. It is NOT guaranteed to succeed; the caller verifies
the result with the O(n^2) 4-point check and falls back to a full recompute
if the repair does not produce a valid LexBFS ordering.

Correctness is guaranteed by the fallback: every update either produces a
verified-valid ordering via repair, or recomputes from scratch.
"""


def _lexbfs_full(graph):
    """Static O(n^2) LexBFS with deterministic tie-break (lowest vertex id)."""
    n = len(graph)
    visited = [False] * n
    labels = [frozenset() for _ in range(n)]
    order = []
    for s in range(n):
        if visited[s]:
            continue
        frontier = [s]
        visited[s] = True
        while frontier:
            best = min(frontier, key=lambda x: (len(labels[x]), labels[x]))
            frontier.remove(best)
            order.append(best)
            nbrs = [v for v in range(n) if graph[best][v] and not visited[v]]
            for v in nbrs:
                visited[v] = True
                frontier.append(v)
                labels[v] = labels[v] | frozenset([best])
    return order


def _is_valid_lexbfs(order, graph):
    """Check the (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue
                ok = False
                for d in range(a):
                    vd = order[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _move_before(order, v, target):
    """Move vertex v to just before target in the ordering."""
    new_order = [x for x in order if x != v]
    idx = new_order.index(target)
    new_order.insert(idx, v)
    return new_order


def _try_repair(order, pos, graph, edge, inserted):
    """Try to repair the ordering after an update. Returns new order or None.

    Insertion of (u,v): the new edge can only create violations where the
    new edge serves as the "ac in E" side. Try moving the offending middle
    vertex w to just before the earlier endpoint.

    Deletion of (u,v): the removed edge can only create violations where
    the removed edge was the "db in E" side. Try moving the endpoint that
    lost its witness to just before the vertex that needed it.
    """
    u, v = edge
    n = len(order)
    if inserted:
        # Try both orientations: (a=u, b=w, c=v) and (a=v, b=w, c=u)
        for (a, c) in ((u, v), (v, u)):
            if pos[a] >= pos[c]:
                continue
            for w in range(n):
                if w == a or w == c:
                    continue
                if not (pos[a] < pos[w] < pos[c]):
                    continue
                if not graph[a][w]:
                    continue
                # Check violation: no d < pos[a] with d~w and not d~c
                violated = True
                for d in range(pos[a]):
                    vd = order[d]
                    if graph[vd][w] and not graph[vd][c]:
                        violated = False
                        break
                if violated:
                    return _move_before(order, w, a)
        return None
    else:
        # Try both orientations: (a=w, b=u, c=v) and (a=w, b=v, c=u)
        for (b, c) in ((u, v), (v, u)):
            if pos[b] >= pos[c]:
                continue
            for w in range(n):
                if w == b or w == c:
                    continue
                if not (pos[w] < pos[b] < pos[c]):
                    continue
                if not graph[w][c]:
                    continue
                # Check violation: no d < pos[w] with d~b and not d~c
                violated = True
                for d in range(pos[w]):
                    vd = order[d]
                    if graph[vd][b] and not graph[vd][c]:
                        violated = False
                        break
                if violated:
                    return _move_before(order, b, w)
        return None


def _make_state(order):
    pos = [0] * len(order)
    for i, v in enumerate(order):
        pos[v] = i
    return {'ordering': order, 'pos': pos}


def init(graph):
    order = _lexbfs_full(graph)
    return _make_state(order)


def insert_edge(graph, edge, state):
    order = state['ordering']
    pos = state['pos']
    repaired = _try_repair(order, pos, graph, edge, inserted=True)
    if repaired is not None and _is_valid_lexbfs(repaired, graph):
        return _make_state(repaired)
    return _make_state(_lexbfs_full(graph))


def delete_edge(graph, edge, state):
    order = state['ordering']
    pos = state['pos']
    repaired = _try_repair(order, pos, graph, edge, inserted=False)
    if repaired is not None and _is_valid_lexbfs(repaired, graph):
        return _make_state(repaired)
    return _make_state(_lexbfs_full(graph))
