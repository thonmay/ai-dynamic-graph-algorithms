"""Dynamic LexBFS ordering (open problem; correctness-first candidate).

Strategy:
- init: run the static LexBFS (labels = bitmask of earlier neighbors;
  pick the unvisited vertex with the minimum label each step) to produce
  a valid ordering.
- insert_edge / delete_edge: check whether the previous ordering is still a
  valid LexBFS ordering of the updated graph (certified by the (LB) 4-point
  property of Corneil-Krueger).  If it is, keep it (no recompute).  If not,
  fall back to a full recompute.

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.
"""


def _recompute(graph):
    """Full static LexBFS via bitmask labels. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    label = [0] * n
    unvisited = set(range(n))
    order = []
    for _ in range(n):
        # pick unvisited vertex with minimum label (tie-break by id)
        v = min(unvisited, key=lambda x: (label[x], x))
        unvisited.remove(v)
        order.append(v)
        bit = 1 << v
        for x in unvisited:
            if graph[v][x]:
                label[x] |= bit
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
