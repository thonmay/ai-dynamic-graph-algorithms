"""Dynamic LexBFS ordering (candidate gen004_c03).

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

The validity check uses Python integers as bitsets: for each position b,
S_a = {d < a : db in E} is built incrementally as a bitmask, and the
violation test "exists c > b with ac in E and S_a subset of N(c)" is a
single integer subset test per c, giving O(n^3 / word) instead of O(n^4).
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
    """Check the (LB) 4-point property with bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Equivalently, a violation exists iff for some a < b with ab not in E
    there is c > b with ac in E and S_a subset of N(c), where
    S_a = {d < a : db in E}.
    """
    n = len(order)
    if n <= 2:
        return True
    # Adjacency bitsets: adj[v] has bit w set iff vw in E.
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        adj[u] = bits

    for b in range(1, n):
        vb = order[b]
        nb_b = adj[vb]
        S = 0  # bitmask of positions d < a with db in E
        for a in range(b):
            va = order[a]
            if (nb_b >> va) & 1:
                S |= 1 << a
                continue
            # ab not in E; check all c > b with ac in E
            nb_a = adj[va]
            for c in range(b + 1, n):
                vc = order[c]
                if not ((nb_a >> vc) & 1):
                    continue
                # violation iff S subset of N(vc)
                if S & ~adj[vc] == 0:
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
