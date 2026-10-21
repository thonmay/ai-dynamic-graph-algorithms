"""Dynamic LexBFS ordering (candidate gen006_c03).

Strategy: maintain a valid LexBFS ordering in the state.  After each edge
update, first try to keep the previous ordering: verify it against the
current graph using the full (LB) 4-point property of Corneil and Krueger
(for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E).  If the ordering is still a valid
LexBFS ordering of the updated graph, return it unchanged (O(n^3) check,
no recompute).  Otherwise fall back to a fresh static partition-refinement
LexBFS (Habib-McConnell-Paul-Viennot style).

The 4-point property is necessary and sufficient for an ordering to be a
LexBFS ordering of the graph (for some start vertex and some tie-breaking),
so the fast path is sound: an ordering that passes the check is accepted
by the verifier, and one that fails is recomputed.
"""


def _is_lexbfs(graph, order):
    """Check the (LB) 4-point property for `order` on `graph`.

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E.
    """
    n = len(order)
    for i in range(n):
        a = order[i]
        ga = graph[a]
        for j in range(i + 1, n):
            b = order[j]
            if ga[b]:
                continue  # ab in E: triple not applicable
            for k in range(j + 1, n):
                c = order[k]
                if not ga[c]:
                    continue  # ac not in E: triple not applicable
                # need d < a with db in E and dc not in E
                ok = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _lexbfs(graph):
    """Static LexBFS: return a valid ordering of all vertices."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets of vertices with identical label
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket, take its smallest vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        v = min(buckets[bi])
        buckets[bi].discard(v)
        order.append(v)

        # refine: for each bucket, split off vertices adjacent to v;
        # the adjacent part (label extended with v, lexicographically
        # larger) keeps the bucket's position, the non-adjacent part
        # goes after it
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = set()
            for x in b:
                if graph[v][x]:
                    nb.add(x)
            if nb:
                rest = b - nb
                new_buckets.append(nb)
                if rest:
                    new_buckets.append(rest)
            else:
                new_buckets.append(b)
        buckets = new_buckets

    return order


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _is_lexbfs(graph, order):
        return {'ordering': order}
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _is_lexbfs(graph, order):
        return {'ordering': order}
    order = _lexbfs(graph)
    return {'ordering': order}
