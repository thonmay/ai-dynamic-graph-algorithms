"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS.
- insert_edge(u,v): if the current ordering is still valid (checked via the
  (LB) 4-point property), keep it. Otherwise recompute.
- delete_edge(u,v): if the current ordering is still valid, keep it.
  Otherwise recompute.

Correctness: we always return a valid LexBFS ordering (either the old one,
which we verified is still valid, or a freshly computed one).
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    ordering = []
    buckets = [[v] for v in range(n)]

    for _ in range(n):
        # find first non-empty bucket
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        x = buckets[bi].pop(0)
        ordering.append(x)
        if not buckets[bi]:
            buckets.pop(bi)
            bi -= 1

        # refine all buckets after position bi by adjacency to x
        new_buckets = []
        for j, b in enumerate(buckets):
            if j < bi:
                new_buckets.append(b)
            else:
                nb = [v for v in b if graph[x][v]]
                nnb = [v for v in b if not graph[x][v]]
                if nb:
                    new_buckets.append(nb)
                if nnb:
                    new_buckets.append(nnb)
        buckets = new_buckets

    return ordering


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > b with ac in E
            for c in range(b + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue  # ac not in E
                # need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _recompute(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    return _recompute(graph)
