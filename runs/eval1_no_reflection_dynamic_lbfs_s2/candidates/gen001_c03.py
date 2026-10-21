"""Dynamic LexBFS ordering.

Strategy:
- init: static LexBFS via partition refinement (O(n+m)).
- insert_edge: try to repair the existing ordering by moving u and v to
  their correct positions.  If the repair fails the (LB) 4-point
  certificate, fall back to a full recompute.
- delete_edge: recompute from scratch.

The (LB) certificate (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns the ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # order: current ordering of all vertices
    order = list(range(n))
    # blocks: list of [start, end) ranges in `order`
    blocks = [[0, n]]

    for _ in range(n):
        # pick the first vertex of the first block
        s = order[blocks[0][0]]

        # refine: split each block into (neighbors of s, non-neighbors of s)
        # neighbors first.  Rebuild the order.
        new_order = []
        new_blocks = []
        for (lo, hi) in blocks:
            nbrs = []
            nonbrs = []
            for j in range(lo, hi):
                v = order[j]
                if graph[s][v]:
                    nbrs.append(v)
                else:
                    nonbrs.append(v)
            start = len(new_order)
            new_order.extend(nbrs)
            new_order.extend(nonbrs)
            end = len(new_order)
            if end > start:
                new_blocks.append([start, end])
        order = new_order
        blocks = new_blocks

    return order


def _is_lexbfs(order, graph):
    """Check the (LB) 4-point certificate. Returns True if valid."""
    n = len(order)
    for ia in range(n):
        a = order[ia]
        for ib in range(ia + 1, n):
            b = order[ib]
            for ic in range(ib + 1, n):
                c = order[ic]
                if graph[a][c] and not graph[a][b]:
                    found = False
                    for id_ in range(ia):
                        d = order[id_]
                        if graph[d][b] and not graph[d][c]:
                            found = True
                            break
                    if not found:
                        return False
    return True


def _try_insert_repair(order, graph, u, v):
    """Try to repair the ordering after inserting edge (u, v).

    The insertion only changes the neighbor sets of u and v.  In a LexBFS
    ordering, the relative order of u and v is determined by their labels.
    After adding the edge, the only possible change is the relative order
    of u and v.  So we try: keep current order, or swap u and v.
    """
    n = len(order)
    pos = {v: i for i, v in enumerate(order)}
    pu, pv = pos[u], pos[v]

    candidates = [list(order)]
    swapped = list(order)
    swapped[pu], swapped[pv] = swapped[pv], swapped[pu]
    candidates.append(swapped)

    for cand in candidates:
        if _is_lexbfs(cand, graph):
            return cand
    return None


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    repaired = _try_insert_repair(order, graph, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    return {'ordering': _lexbfs(graph)}


def delete_edge(graph, edge, state):
    return {'ordering': _lexbfs(graph)}
