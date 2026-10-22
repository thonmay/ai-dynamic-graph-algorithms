"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering across edge updates. After an
update, first check whether the previous ordering is still a valid LexBFS
ordering of the new graph using the (LB) 4-point property of Corneil and
Krueger:

    for all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

If the ordering is still valid, return it unchanged (O(n^2) check, no
recomputation). Only if the check fails do we recompute a static LexBFS
ordering via partition refinement, using the previous ordering as a hint
for the start vertex and for tie-breaking.

State: dict with 'ordering' (list of all n vertices, a valid LexBFS
ordering) and 'n'.
"""


def _refine(buckets, v, graph):
    """Split every bucket by adjacency to v. Each bucket is replaced
    in place by its neighbor part (first) and its non-neighbor part
    (second), at the same queue position."""
    out = []
    for b in buckets:
        if not b:
            continue
        nb = [x for x in b if graph[x][v]]
        non = [x for x in b if not graph[x][v]]
        if nb:
            out.append(nb)
        if non:
            out.append(non)
    return out


def _lexbfs(graph, n, start, rank):
    """Static LexBFS via partition refinement.

    Buckets are kept as lists (not sets) so that refinement is
    deterministic and tie-breaking by (rank, id) is well-defined.
    """
    if n == 0:
        return []

    # buckets: list of lists of unprocessed vertices, in queue order
    buckets = [[v for v in range(n) if v != start]]

    order = [start]

    # the start vertex's adjacency must split the initial bucket
    buckets = _refine(buckets, start, graph)

    for _ in range(n - 1):
        # pick next vertex: first non-empty bucket, min by (rank, id)
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = min(buckets[bi], key=lambda x: (rank[x], x))
        buckets[bi].remove(v)
        order.append(v)

        # refine all buckets by adjacency to v, each bucket replaced
        # in place by (neighbor part, non-neighbor part)
        buckets = _refine(buckets, v, graph)

    return order


def _is_valid_lexbfs(order, graph, n):
    """Check the (LB) 4-point property of Corneil and Krueger.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True iff the ordering is a valid LexBFS ordering.
    """
    if n == 0:
        return True
    if len(order) != n:
        return False
    if sorted(order) != list(range(n)):
        return False

    # Direct O(n^3) check with early exit: iterate over triples
    # (a, b, c) with a < b < c in position.
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # ab in E, condition not triggered
            # ab not in E; now check all c > b
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue  # ac not in E, condition not triggered
                # ac in E and ab not in E: need d < a with db in E and dc not in E
                found = False
                for d_idx in range(i):
                    d = order[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _recompute(graph, state):
    n = state['n']
    hint = state['ordering']
    if not hint:
        start = 0
        rank = [i for i in range(n)]
    else:
        start = hint[0]
        rank = [0] * n
        for i, v in enumerate(hint):
            rank[v] = i
    order = _lexbfs(graph, n, start, rank)
    return {'ordering': order, 'n': n}


def init(graph):
    n = len(graph)
    order = _lexbfs(graph, n, 0, [i for i in range(n)])
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    # Check if the previous ordering is still valid
    if _is_valid_lexbfs(order, graph, n):
        return state
    return _recompute(graph, state)


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    # Check if the previous ordering is still valid
    if _is_valid_lexbfs(order, graph, n):
        return state
    return _recompute(graph, state)
