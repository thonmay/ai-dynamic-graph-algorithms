"""Dynamic LexBFS ordering (candidate gen001_c03).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m).
- insert_edge(u,v): if the current ordering is still valid (checked via the
  (LB) 4-point property), keep it.  Otherwise, recompute from scratch.
- delete_edge(u,v): deleting an edge can only destroy validity, so always
  recompute from scratch.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
A vertex ordering is a LexBFS ordering iff it satisfies (LB).
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    buckets = [set(range(n))]
    order = []

    for v in range(n):
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        b = buckets[bi]
        x = min(b)
        b.remove(x)
        order.append(x)
        nb = graph[x]
        new_buckets = []
        for bj in buckets:
            if not bj:
                continue
            inside = set(w for w in bj if nb[w])
            outside = bj - inside
            if inside:
                new_buckets.append(inside)
            if outside:
                new_buckets.append(outside)
        buckets = new_buckets
    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Optimized: for each b, build S_a = {d < a : db in E} incrementally.
    For each a < b with ab not in E, check if there exists c > b with
    ac in E and S_a subset of N(c) (violation).
    """
    n = len(order)
    if n <= 2:
        return True
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)

    for b in range(1, n):
        vb = order[b]
        S = set()  # S_a = {d < a : db in E}
        for a in range(b):
            va = order[a]
            if va in adj[vb]:
                S.add(a)
                continue
            # ab not in E; check all c > b with ac in E
            if not S:
                for c in range(b + 1, n):
                    if order[c] in adj[va]:
                        return False
            else:
                for c in range(b + 1, n):
                    vc = order[c]
                    if vc not in adj[va]:
                        continue
                    subset = True
                    for d in S:
                        if order[d] not in adj[vc]:
                            subset = False
                            break
                    if subset:
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
    order = _lexbfs(graph)
    return {'ordering': order}
