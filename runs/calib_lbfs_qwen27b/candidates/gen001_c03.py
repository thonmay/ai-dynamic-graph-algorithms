"""Dynamic LexBFS ordering.

Maintain a valid LexBFS ordering under edge insertions/deletions.

On each update: check the (LB) 4-point property on the current ordering.
If it still holds, keep it (no recompute). If it fails, recompute a
LexBFS ordering from scratch using the old ordering as the tie-break.

The LexBFS computation uses the bucket-refinement algorithm of
Habib-McConnell-Paul-Viennot, O(n^2) with matrix input.
"""


def _lexbfs(graph, n, tiebreak=None):
    """Bucket-refinement LexBFS on an adjacency matrix.

    tiebreak: optional list of vertices; used as the rank order within
    buckets and to pick the start vertex. Any tie-break yields a valid
    LexBFS ordering.
    """
    if n == 0:
        return []
    if n == 1:
        return [0]

    if tiebreak is not None:
        rank = {v: i for i, v in enumerate(tiebreak)}
    else:
        rank = {v: v for v in range(n)}

    # One bucket with all vertices in rank order.
    allv = list(range(n))
    allv.sort(key=lambda v: rank[v])
    buckets = [allv]

    order = []
    remaining = n
    while remaining > 0:
        # Find first non-empty bucket.
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        B = buckets[bi]
        v = B[0]
        B.pop(0)
        order.append(v)
        remaining -= 1

        # Refine every bucket: split into (N(v), non-N(v)), N(v) first,
        # preserving rank order within each part.
        row = graph[v]
        for i in range(len(buckets)):
            Bk = buckets[i]
            if not Bk:
                continue
            j = 0
            for x in Bk:
                if row[x]:
                    Bk[j] = x
                    j += 1
            if 0 < j < len(Bk):
                buckets[i:i + 1] = [Bk[:j], Bk[j:]]

    return order


def _check_lb(graph, n, order):
    """Check the (LB) 4-point property of Corneil-Krueger.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue
                found = False
                for d in range(a):
                    vd = order[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    order = _lexbfs(graph, n)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    n = state['n']
    if _check_lb(graph, n, order):
        return state
    order = _lexbfs(graph, n, tiebreak=order)
    state = dict(state)
    state['ordering'] = order
    return state


def delete_edge(graph, edge, state):
    order = state['ordering']
    n = state['n']
    if _check_lb(graph, n, order):
        return state
    order = _lexbfs(graph, n, tiebreak=order)
    state = dict(state)
    state['ordering'] = order
    return state
