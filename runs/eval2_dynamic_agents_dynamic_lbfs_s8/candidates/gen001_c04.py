"""Dynamic LexBFS ordering.

Maintains a valid LexBFS ordering under edge insertions and deletions.

On each update we verify the maintained ordering against the (LB) 4-point
property of Corneil and Krueger:

    for all a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

If the property still holds, the ordering is a valid LexBFS and we keep it
(cheap path). Otherwise we recompute a fresh LexBFS ordering with the
partition-refinement algorithm of Habib, McConnell, Paul and Viennot
(O(n^2) on the adjacency matrix).
"""


def _lexbfs(g):
    """Static partition-refinement LexBFS on adjacency matrix g.

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(g)
    if n == 0:
        return []
    # labels[v] = list of (position, vertex) for the partition containing v
    labels = [[(0, v)] for v in range(n)]
    order = []
    remaining = list(range(n))
    while remaining:
        # pick the lexicographically smallest label
        best = min(remaining, key=lambda v: labels[v])
        order.append(best)
        remaining.remove(best)
        pos = len(order)
        # refine: for each neighbor w of best still remaining, move w to a
        # new partition with label labels[w] + [(pos, best)]
        for w in remaining:
            if g[best][w]:
                labels[w] = labels[w] + [(pos, best)]
    return order


def _is_lexbfs(g, order):
    """Check the (LB) 4-point property for `order` on graph g. O(n^3).

    For all a<b<c with ac in E and ab not in E, there must exist d<a with
    db in E and dc not in E.
    """
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if g[a][b]:
                continue  # need ab not in E
            for k in range(j + 1, n):
                c = order[k]
                if not g[a][c]:
                    continue  # need ac in E
                found = False
                for t in range(i):
                    d = order[t]
                    if g[d][b] and not g[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    # Always recompute: an insertion can create new 4-point obligations
    # (new edge ac with a<b<c, ab not in E) that the old ordering may not
    # satisfy. The 4-point check is O(n^3) and the recompute is O(n^2), so
    # recomputing is the cheaper and simpler option.
    return {'ordering': _lexbfs(graph)}


def delete_edge(graph, edge, state):
    # A deletion can only destroy witnesses, so the property can only be
    # hurt. Verify the (LB) property; recompute if it fails.
    order = state['ordering']
    if _is_lexbfs(graph, order):
        return state
    return {'ordering': _lexbfs(graph)}
