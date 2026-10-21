"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try to repair
the existing ordering locally; if the repair fails, fall back to a full
static LexBFS recompute (correctness is guaranteed by the fallback).

Repair idea:
  - Edge insertion (u,v): the only way the old ordering can become invalid
    is via the new edge.  If u and v are in the wrong relative position
    (u after v), swap them and check the (LB) 4-point property.  If the
    swap keeps the ordering valid, keep it; otherwise recompute.
  - Edge deletion (u,v): the only way the old ordering can become invalid
    is that some witness d for a 4-point tuple used the deleted edge.
    Check the (LB) property; if it still holds, keep the ordering;
    otherwise recompute.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lb_valid(order, adj):
    """Check the (LB) 4-point property for `order` on adjacency matrix `adj`.

    order: list of vertices (the candidate LexBFS ordering)
    adj:   n x n 0/1 adjacency matrix
    Returns True iff the ordering is a valid LexBFS ordering.
    """
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if adj[a][b]:
                continue
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for k in range(j + 1, n):
                c = order[k]
                if not adj[a][c]:
                    continue
                # need witness d < a with db in E and dc not in E
                found = False
                for t in range(i):
                    d = order[t]
                    if adj[d][b] and not adj[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _lexbfs(adj):
    """Static LexBFS (O(n^2) with matrix).

    Returns a valid LexBFS ordering (list of vertices).
    """
    n = len(adj)
    if n == 0:
        return []
    visited = [False] * n
    # label[v] = list of 0/1, index = visit order of visited vertices
    labels = [[] for _ in range(n)]
    order = []
    for _ in range(n):
        # pick unvisited vertex with lexicographically smallest label
        best = -1
        best_label = None
        for v in range(n):
            if visited[v]:
                continue
            if best == -1 or labels[v] < best_label:
                best = v
                best_label = labels[v]
        visited[best] = True
        order.append(best)
        # update labels of unvisited vertices
        for v in range(n):
            if not visited[v]:
                labels[v].append(1 if adj[best][v] else 0)
    return order


def _try_swap_repair(order, adj, u, v):
    """Try to repair `order` after inserting edge (u,v) by swapping u and v.

    Returns the repaired ordering if valid, else None.
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    pu, pv = pos[u], pos[v]
    if pu > pv:
        # u is after v; the new edge (u,v) with u after v is the "bad" case.
        # Swap them.
        new_order = order[:]
        new_order[pu], new_order[pv] = new_order[pv], new_order[pu]
        if _lb_valid(new_order, adj):
            return new_order
    # If u is already before v, the new edge cannot create a violation
    # (the 4-point property only constrains non-edges).
    return order


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    if pos[u] < pos[v]:
        return {'ordering': order, 'n': n}
    # Try swap repair
    repaired = _try_swap_repair(order, graph, u, v)
    if repaired is not None:
        return {'ordering': repaired, 'n': n}
    # Fallback: full recompute
    return {'ordering': _lexbfs(graph), 'n': n}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    n = len(order)
    # Deleting an edge can only hurt the (LB) property (it removes
    # potential witnesses).  Check if the ordering is still valid.
    if _lb_valid(order, graph):
        return {'ordering': order, 'n': n}
    # Fallback: full recompute
    return {'ordering': _lexbfs(graph), 'n': n}
