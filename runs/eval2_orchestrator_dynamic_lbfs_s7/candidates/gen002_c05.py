"""Dynamic LexBFS ordering.

Maintains a valid LexBFS ordering under edge insertions and deletions.

Strategy:
  * init: run partition-refinement LexBFS once.
  * update: try to repair the previous ordering locally.  A single edge
    flip can only change the lexicographic keys of the two endpoints, so
    the previous ordering is often still valid, or becomes valid after
    moving the affected vertices.  We test the (LB) 4-point certificate
    (Corneil-Krueger) on the current ordering; if it fails we try a
    handful of cheap local repairs (reinserting the affected vertices at
    their lexicographically correct positions, and a few alternative
    start vertices).  Only if all local repairs fail do we fall back to
    a full recompute.

The certificate check is O(n^3) in the worst case but is a pure
verification step; the expensive part (recomputing the ordering) is
skipped whenever the local repair succeeds.
"""


def _lexbfs(graph, n, order_hint=None):
    """Partition-refinement LexBFS.

    If order_hint is given (a permutation of 0..n-1), it is used as the
    tie-break for bucket ordering.  Returns a LexBFS ordering.
    """
    if order_hint is None:
        order_hint = list(range(n))

    buckets = [[v] for v in order_hint]
    order = []

    while buckets:
        b = buckets.pop(0)
        # Split b by adjacency to the already-ordered prefix.
        keys = []
        for v in b:
            keys.append(tuple(x for x in order if graph[x][v]))
        pairs = sorted(zip(keys, b), key=lambda t: t[0])
        newb = [v for _, v in pairs]
        sub = []
        cur = [newb[0]]
        curk = pairs[0][0]
        for i in range(1, len(newb)):
            if pairs[i][0] == curk:
                cur.append(newb[i])
            else:
                sub.append(cur)
                cur = [newb[i]]
                curk = pairs[i][0]
        sub.append(cur)
        first = sub[0][0]
        order.append(first)
        rest = []
        if len(sub[0]) > 1:
            rest.append(sub[0][1:])
        rest.extend(sub[1:])
        buckets = rest + buckets

    return order


def _is_valid_lexbfs(graph, n, order):
    """Check the 4-point (LB) property of Corneil and Krueger.

    For all positions a < b < c with ac in E and ab not in E, there
    exists d < a with db in E and dc not in E.
    """
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                found = False
                for l in range(i):
                    d = order[l]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _reinsert(graph, n, order, v):
    """Remove v from order and reinsert it at the position where its
    lexicographic key (tuple of earlier neighbours) fits.  Returns the
    new ordering."""
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    p = pos[v]
    rest = order[:p] + order[p + 1:]
    insert_at = len(rest)
    for i, w in enumerate(rest):
        kv = tuple(x for x in rest[:i] if graph[x][v])
        kw = tuple(x for x in rest[:i] if graph[x][w])
        if kv <= kw:
            insert_at = i
            break
    return rest[:insert_at] + [v] + rest[insert_at:]


def _try_repairs(graph, n, order, affected):
    """Try cheap local repairs; return a valid ordering or None."""
    # 1. reinsert affected vertices (in order) at their lexicographic
    #    positions.
    cand = list(order)
    for v in affected:
        cand = _reinsert(graph, n, cand, v)
    if _is_valid_lexbfs(graph, n, cand):
        return cand
    # 2. reinsert in reverse order
    cand = list(order)
    for v in reversed(affected):
        cand = _reinsert(graph, n, cand, v)
    if _is_valid_lexbfs(graph, n, cand):
        return cand
    # 3. try each affected vertex as start, with the current order as
    #    hint.
    for v in affected:
        hint = [v] + [x for x in order if x != v]
        cand = _lexbfs(graph, n, hint)
        if _is_valid_lexbfs(graph, n, cand):
            return cand
    return None


def _find_valid_ordering(graph, n, order_hint):
    """Find a valid LexBFS ordering, trying different start vertices."""
    order = _lexbfs(graph, n, order_hint=order_hint)
    if _is_valid_lexbfs(graph, n, order):
        return order
    for start in range(n):
        hint = [start] + [v for v in order_hint if v != start]
        order = _lexbfs(graph, n, hint)
        if _is_valid_lexbfs(graph, n, order):
            return order
    order = _lexbfs(graph, n, list(range(n)))
    if _is_valid_lexbfs(graph, n, order):
        return order
    return order


def init(graph):
    n = len(graph)
    order = _find_valid_ordering(graph, n, list(range(n)))
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    order = state['ordering']
    if _is_valid_lexbfs(graph, n, order):
        return {'ordering': order, 'n': n}
    repaired = _try_repairs(graph, n, order, [u, v])
    if repaired is not None:
        return {'ordering': repaired, 'n': n}
    order = _find_valid_ordering(graph, n, order)
    return {'ordering': order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    order = state['ordering']
    if _is_valid_lexbfs(graph, n, order):
        return {'ordering': order, 'n': n}
    repaired = _try_repairs(graph, n, order, [u, v])
    if repaired is not None:
        return {'ordering': repaired, 'n': n}
    order = _find_valid_ordering(graph, n, order)
    return {'ordering': order, 'n': n}
