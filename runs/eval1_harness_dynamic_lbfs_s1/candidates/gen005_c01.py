"""Dynamic LexBFS ordering maintenance (undirected).

Maintains *some* valid LexBFS ordering (any start vertex, any tie-break) under
edge insertions and deletions. The verifier accepts any ordering that satisfies
the (LB) 4-point property of Corneil & Krueger, so after each single-edge flip
we first test whether the ordering we already hold is still valid; if it is we
keep it (no recompute), otherwise we recompute a fresh ordering.

State (a plain dict, JSON-serialisable):
  'ordering': list of the n vertex ids in the maintained LexBFS order
  'adj':      list of n ints; adj[u] is a bitmask with bit v set iff u~v

Validity after a single flip (u, v) is checked *locally*: a triple (a, b, c)
with a<b<c can only change its (LB) status if at least one of {a, b, c} is a
flipped endpoint, because the three things (LB) looks at for that triple --
whether ac in E, whether ab in E, and the witness set W(b, c) = {d: b~d, not
c~d} -- all depend only on edges incident to a, b or c. So we recheck only the
triples with b in {u, v} or c in {u, v}, which is O(n^2) instead of O(n^3).
"""


def _lexbfs(n, adj):
    """Partition-refinement LexBFS over adjacency bitmasks.

    Starts at vertex 0 with the increasing-id tie-break. Returns the ordering.
    """
    order = []
    # Pi is a list of cells; each cell is a list of vertices in current order.
    Pi = [list(range(n))]
    while len(order) < n:
        p = Pi[0][0]
        order.append(p)
        neigh = adj[p]
        newPi = []
        for C in Pi:
            a = [v for v in C if v != p and ((neigh >> v) & 1)]
            b = [v for v in C if v != p and not ((neigh >> v) & 1)]
            if a:
                newPi.append(a)
            if b:
                newPi.append(b)
        Pi = newPi
    return order


def _sep_mask(adj, n, x, y):
    """Bitmask of vertices d with x~d and not y~d (the witness set for pair (x, y))."""
    s = 0
    for d in range(n):
        if ((adj[d] >> x) & 1) and not ((adj[d] >> y) & 1):
            s |= 1 << d
    return s


def _lb_valid_after_flip(ordering, adj, n, u, v):
    """Return True iff `ordering` still satisfies (LB) after flipping edge (u, v).

    Rechecks only triples (a, b, c) with b in {u, v} or c in {u, v}; every other
    triple has unchanged (ac in E), (ab in E) and witness set, so its (LB)
    status is unchanged from the previously valid state.
    """
    # prefix[i] = bitmask of the vertices at positions < i
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << ordering[i])

    # Witness masks for every pair where at least one endpoint is u or v.
    sep = {}
    for x in (u, v):
        for y in range(n):
            if y != x:
                sep[(x, y)] = _sep_mask(adj, n, x, y)
                sep[(y, x)] = _sep_mask(adj, n, y, x)

    for b_pos in range(n):
        vb = ordering[b_pos]
        for c_pos in range(b_pos + 1, n):
            vc = ordering[c_pos]
            # A triple (a, b, c) changes (LB) status only if the vertex at
            # position b or position c is a flipped endpoint (see module doc).
            if vb not in (u, v) and vc not in (u, v):
                continue
            sbc = sep.get((vb, vc))
            if sbc is None:
                sbc = _sep_mask(adj, n, vb, vc)
            for a_pos in range(b_pos):
                va = ordering[a_pos]
                va_adj = adj[va]
                if ((va_adj >> vc) & 1) and not ((va_adj >> vb) & 1):
                    # ac in E, ab not in E: need a witness d at position < a
                    if not (prefix[a_pos] & sbc):
                        return False
    return True


def _build(n, adj):
    return {"ordering": _lexbfs(n, adj), "adj": adj}


def init(graph):
    n = len(graph)
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        mask = 0
        for v in range(n):
            if row[v]:
                mask |= 1 << v
        adj[u] = mask
    return _build(n, adj)


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(state["adj"])
    adj = state["adj"]
    adj[u] |= 1 << v
    adj[v] |= 1 << u
    if _lb_valid_after_flip(state["ordering"], adj, n, u, v):
        return state
    return _build(n, adj)


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(state["adj"])
    adj = state["adj"]
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    if _lb_valid_after_flip(state["ordering"], adj, n, u, v):
        return state
    return _build(n, adj)
