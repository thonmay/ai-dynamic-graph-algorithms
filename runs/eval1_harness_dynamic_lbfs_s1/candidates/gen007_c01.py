"""Dynamic LexBFS ordering maintenance (undirected).

Maintains *some* valid LexBFS ordering (any start vertex, any tie-break) under
edge insertions and deletions. The verifier accepts any ordering that satisfies
the (LB) 4-point property of Corneil & Krueger, so after each single-edge flip
we first test whether the ordering we already hold is still valid; if it is we
keep it (no recompute), otherwise we recompute a fresh ordering.

State (a plain dict, JSON-serialisable):
  'ordering': list of the n vertex ids in the maintained LexBFS order
  'adj':      list of n ints; adj[u] is a bitmask with bit v set iff u~v

The (LB) test uses the identity that the witness set of a pair (b, c),
  W(b, c) = { d : b~d and not c~d },
is exactly N(b) \\ N(c) = adj[b] & ~adj[c] (a bitmask), so each (LB) triple
test is a handful of bit operations.
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


def _lb_valid(ordering, adj, n):
    """Return True iff `ordering` satisfies the (LB) 4-point property.

    (LB): for all positions a < b < c with ac in E and ab not in E, there is a
    d at position < a with db in E and dc not in E.

    prefix[a] is the bitmask of the vertices at positions < a. The witness set
    W(b, c) = N(b) \\ N(c) = adj[b] & ~adj[c], so the witness exists before
    position a iff prefix[a] & (adj[b] & ~adj[c]) is non-zero.
    """
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << ordering[i])

    for a in range(n):
        va = ordering[a]
        va_adj = adj[va]
        pa = prefix[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if (va_adj >> vb) & 1:
                continue  # ab in E: (LB) does not constrain this triple
            vb_adj = adj[vb]
            for c in range(b + 1, n):
                vc = ordering[c]
                if not ((va_adj >> vc) & 1):
                    continue  # ac not in E
                if not (pa & (vb_adj & ~adj[vc])):
                    return False  # no separating witness before a
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
    if _lb_valid(state["ordering"], adj, n):
        return state
    return _build(n, adj)


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(state["adj"])
    adj = state["adj"]
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    if _lb_valid(state["ordering"], adj, n):
        return state
    return _build(n, adj)
