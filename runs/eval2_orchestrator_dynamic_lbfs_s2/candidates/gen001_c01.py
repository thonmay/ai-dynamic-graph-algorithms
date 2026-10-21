"""Dynamic LexBFS ordering (open problem; this candidate is a correct baseline).

Strategy: maintain a valid LexBFS ordering in the state. After each edge
update, verify the ordering against the (LB) 4-point property of Corneil and
Krueger: for all positions a < b < c with ac in E and ab not in E, there
exists d < a with db in E and dc not in E. If the ordering is still valid,
keep it (no recompute). Otherwise recompute a fresh LexBFS ordering with the
static partition-refinement algorithm (Habib-McConnell-Paul-Viennot style,
O(n+m)).

This is correct for all graphs and updates; the only cost question is how
often the 4-point check fails and forces a recompute.
"""


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

        # refine: for each bucket, split off vertices adjacent to v
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
                if rest:
                    new_buckets.append(rest)
                new_buckets.append(nb)
            else:
                new_buckets.append(b)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property: for all a < b < c (positions) with
    ac in E and ab not in E, exists d < a with db in E and dc not in E."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue  # ab in E, condition not triggered
            # ab not in E; need: for every c > b with ac in E,
            # exists d < a with db in E and dc not in E
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue
                # ac in E, ab not in E: need witness d < a
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
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    order = _lexbfs(graph)
    return {'ordering': order}
