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
    last = None

    while buckets:
        b = buckets.pop(0)
        # Split b by adjacency to the most recently selected vertex.
        if last is None:
            # First bucket: no refinement, take the first vertex.
            first = b[0]
            order.append(first)
            if len(b) > 1:
                buckets = [b[1:]] + buckets
            last = first
            continue
        nb = [v for v in b if graph[last][v]]
        nnb = [v for v in b if not graph[last][v]]
        # Select the first vertex of the adjacent part if non-empty,
        # otherwise the first vertex of the non-adjacent part.
        if nb:
            first = nb[0]
            rest = [nb[1:]] if len(nb) > 1 else []
            if nnb:
                rest.append(nnb)
        else:
            first = nnb[0]
            rest = [nnb[1:]] if len(nnb) > 1 else []
        order.append(first)
        buckets = rest + buckets
        last = first

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
