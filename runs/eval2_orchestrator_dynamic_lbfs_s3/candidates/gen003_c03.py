"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, check whether the
old ordering is still a valid LexBFS ordering via the (LB) 4-point property.
If it is, return the state unchanged (no recompute).
If not, fall back to a full O(n^2) partition-refinement LexBFS recompute.

The (LB) property (Corneil & Krueger): for all positions a < b < c in the
ordering with ac in E and ab not in E, there exists d < a with db in E and
dc not in E.  An ordering is a valid LexBFS ordering iff it satisfies (LB).

Optimizations over the naive O(n^4) check:
- Bitset representation of the adjacency matrix (Python ints) for O(1)
  membership tests.
- Precompute, for each position a, the set of positions d < a that are
  adjacent to order[a] (as a bitset).  The (LB) witness test for a triple
  (a, b, c) then becomes: (N_d[a] & N_b & ~N_c) != 0, i.e. some d < a is
  adjacent to b but not to c.  This is O(1) big-int ops per triple, so the
  whole check is O(n^3 / word) instead of O(n^4).
"""


def _check_lb(order, adj):
    """Check the (LB) 4-point property. Return True if valid."""
    n = len(order)
    if n <= 2:
        return True
    # N[v] = bitset of neighbors of vertex v
    N = [0] * n
    for u in range(n):
        row = adj[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        N[u] = bits
    # Npos[i] = bitset of positions d < i such that order[d] is adjacent to order[i]
    Npos = [0] * n
    for i in range(n):
        vi = order[i]
        bits = 0
        for d in range(i):
            if N[vi] >> order[d] & 1:
                bits |= 1 << d
        Npos[i] = bits
    for a in range(n):
        va = order[a]
        Na = N[va]
        # positions b > a where ab not in E
        for b in range(a + 1, n):
            vb = order[b]
            if Na >> vb & 1:
                continue  # ab in E, condition not triggered
            # ab not in E; need: for all c > b with ac in E,
            #   exists d < a with db in E and dc not in E.
            # witness set for this (a,b): W = Npos[a] & N[vb]  (positions d<a adj to b)
            # For each c > b with ac in E, we need W & ~N[vc] != 0.
            W = Npos[a] & N[vb]
            if W == 0:
                # no d < a adjacent to b at all -> any c > b with ac in E fails
                for c in range(b + 1, n):
                    vc = order[c]
                    if Na >> vc & 1:
                        return False
                continue
            # For each c > b with ac in E, check W & ~N[vc] != 0
            for c in range(b + 1, n):
                vc = order[c]
                if not (Na >> vc & 1):
                    continue  # ac not in E
                if (W & ~N[vc]) == 0:
                    return False
    return True


def _lexbfs_full(adj):
    """Full O(n^2) LexBFS via partition refinement. Returns ordering list."""
    n = len(adj)
    if n == 0:
        return []
    # buckets: list of lists of vertices with the same label so far
    buckets = [[v for v in range(n)]]
    order = []

    while buckets:
        # pick first vertex of first bucket
        v = buckets[0][0]
        buckets[0].pop(0)
        if not buckets[0]:
            buckets.pop(0)
        order.append(v)
        # refine all remaining buckets by adjacency to v
        new_buckets = []
        for b in buckets:
            b1 = [x for x in b if adj[v][x]]
            b0 = [x for x in b if not adj[v][x]]
            if b1:
                new_buckets.append(b1)
            if b0:
                new_buckets.append(b0)
        buckets = new_buckets

    return order


def init(graph):
    n = len(graph)
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _check_lb(order, graph):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph)}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _check_lb(order, graph):
        return state
    order = _lexbfs_full(graph)
    return {'ordering': order, 'n': len(graph)}
