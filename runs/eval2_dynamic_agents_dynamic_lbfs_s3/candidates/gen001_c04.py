"""Dynamic LexBFS ordering (open problem; correctness-first candidate).

Strategy:
- init: run the static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot
  style, with a deterministic tie-break) to produce a valid ordering.
- insert_edge / delete_edge: check whether the previous ordering is still a
  valid LexBFS ordering of the updated graph (certified by the (LB) 4-point
  property of Corneil-Krueger).  If it is, keep it (no recompute).  If not,
  fall back to a full recompute.

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.
"""


def _recompute(graph):
    """Full static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    # buckets: list of lists of vertices with equal label (set of earlier
    # neighbors).  The first non-empty bucket is chosen (deterministic
    # tie-break by the order in which buckets were created).
    buckets = [[v] for v in range(n)]
    order = []

    for _ in range(n):
        # pick first non-empty bucket
        b = None
        for bucket in buckets:
            if bucket:
                b = bucket
                break
        v = b[0]
        b.remove(v)
        order.append(v)
        # refine buckets by adjacency to v: neighbors of v get a new label
        # (label gains v), non-neighbors keep theirs.
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            neigh = [x for x in bucket if graph[v][x]]
            rest = [x for x in bucket if not graph[v][x]]
            if neigh:
                if rest:
                    new_buckets.append(rest)
                new_buckets.append(neigh)
            else:
                new_buckets.append(bucket)
        buckets = new_buckets
    return order


def _check_lb(order, graph):
    """Verify the (LB) 4-point property. Returns True iff valid."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue
            # ab not in E; for all c > b with ac in E, need d < a with
            # db in E and dc not in E.
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                ok = False
                for d in order[:i]:
                    if graph[d][b] and not graph[d][c]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def init(graph):
    order = _recompute(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = list(state['ordering'])
    if _check_lb(order, graph):
        return {'ordering': order}
    order = _recompute(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = list(state['ordering'])
    if _check_lb(order, graph):
        return {'ordering': order}
    order = _recompute(graph)
    return {'ordering': order}
