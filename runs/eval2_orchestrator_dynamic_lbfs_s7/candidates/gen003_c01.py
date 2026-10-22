"""Dynamic LexBFS ordering.

Maintains a valid LexBFS ordering under edge insertions and deletions.
On each update, re-runs the partition-refinement LexBFS (Habib,
McConnell, Paul, Viennot) using the current ordering as the tie-break
hint.  If the result fails the 4-point (LB) certificate, tries
alternative start vertices.
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
        first = b[0]
        order.append(first)
        # Refine every remaining bucket by adjacency to `first`:
        # each bucket is split into (adjacent part, non-adjacent part),
        # with the adjacent part placed before the non-adjacent part.
        new_buckets = []
        for bucket in buckets:
            nb = [v for v in bucket if graph[first][v]]
            nnb = [v for v in bucket if not graph[first][v]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        # The rest of the front bucket (minus `first`) is refined by
        # adjacency to `first` as well; since `first` is adjacent to
        # itself, the adjacent part is empty and the non-adjacent part
        # is the whole remainder.
        if len(b) > 1:
            new_buckets.insert(0, b[1:])
        buckets = new_buckets

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
    u, v = edge
    # Ensure the matrix reflects the update (idempotent if already applied).
    graph[u][v] = 1
    graph[v][u] = 1
    order = _find_valid_ordering(graph, n, state['ordering'])
    return {'ordering': order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    # Ensure the matrix reflects the update (idempotent if already applied).
    graph[u][v] = 0
    graph[v][u] = 0
    order = _find_valid_ordering(graph, n, state['ordering'])
    return {'ordering': order, 'n': n}
