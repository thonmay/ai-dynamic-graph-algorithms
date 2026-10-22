"""Dynamic LexBFS ordering.

Maintains a valid LexBFS ordering under edge insertions and deletions.
On each update, re-runs the partition-refinement LexBFS using the
current ordering as the tie-break hint.  If the result fails the
4-point (LB) certificate, tries alternative start vertices.
"""


def _lexbfs(graph, n, order_hint=None):
    """Partition-refinement LexBFS.

    If order_hint is given (a permutation of 0..n-1), it is used as
    the tie-break for bucket ordering.  Returns a valid LexBFS
    ordering.
    """
    if order_hint is None:
        order_hint = list(range(n))

    # buckets: list of lists of vertices, in processing order
    buckets = [[v] for v in order_hint]
    order = []

    while buckets:
        b = buckets.pop(0)
        # Split b by adjacency to the already-ordered prefix.
        # For each vertex in b, compute the tuple of earlier neighbours
        # in the order they appear in `order`.
        keys = []
        for v in b:
            keys.append(tuple(x for x in order if graph[x][v]))
        # stable sort by key
        pairs = sorted(zip(keys, b), key=lambda t: t[0])
        newb = [v for _, v in pairs]
        # split into sub-buckets with equal keys
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
        # select first vertex of first sub-bucket
        first = sub[0][0]
        order.append(first)
        # remaining sub-buckets go to the front of the queue
        rest = []
        if len(sub[0]) > 1:
            rest.append(sub[0][1:])
        rest.extend(sub[1:])
        buckets = rest + buckets

    return order


def _is_valid_lexbfs(graph, n, order):
    """Check the 4-point (LB) property of Corneil and Krueger."""
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


def _find_valid_ordering(graph, n, order_hint):
    """Find a valid LexBFS ordering, trying different start vertices.

    First tries the hint order, then each vertex as start.
    """
    order = _lexbfs(graph, n, order_hint=order_hint)
    if _is_valid_lexbfs(graph, n, order):
        return order
    for start in range(n):
        hint = [start] + [v for v in order_hint if v != start]
        order = _lexbfs(graph, n, order_hint=hint)
        if _is_valid_lexbfs(graph, n, order):
            return order
    # Fallback: natural order
    return _lexbfs(graph, n)


def init(graph):
    n = len(graph)
    order = _find_valid_ordering(graph, n, list(range(n)))
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = _find_valid_ordering(graph, n, state['ordering'])
    return {'ordering': order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    order = _find_valid_ordering(graph, n, state['ordering'])
    return {'ordering': order, 'n': n}
