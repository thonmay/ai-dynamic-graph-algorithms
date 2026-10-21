"""Dynamic LexBFS ordering (gen004_c01).

Derived from the parent's check-then-recompute scheme, with two changes:

1. The (LB) 4-point validity check is vectorized with bitsets (Python ints
   as bit vectors), so a full check costs O(n^2 / w) instead of O(n^3).
   This makes "keep the old ordering if it is still valid" cheap enough to
   be worthwhile on dense graphs, and it is exact (no heuristics).

2. The static LexBFS (Habib-McConnell-Paul-Viennot partition refinement)
   is unchanged and O(n+m) via adjacency lists.

State: {'ordering': list, 'adj': list[set]}.
"""


def _adj_lists(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def _lexbfs(adj):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(adj)
    if n == 0:
        return []

    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        s = buckets[0][0]
        order.append(s)
        buckets[0] = buckets[0][1:]
        if not buckets[0]:
            buckets = buckets[1:]

        new_buckets = []
        for b in buckets:
            n_part = [v for v in b if v in adj[s]]
            nb_part = [v for v in b if v not in adj[s]]
            if n_part:
                new_buckets.append(n_part)
            if nb_part:
                new_buckets.append(nb_part)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(order, adj):
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Bitset trick: for each position a, let
      S_a = { c > a : ac in E }
      T_a = { b > a : ab not in E }
    The ordering is valid iff for every a,
      for every b in T_a,  (N(b) & ~S_a) & prefix_mask[a] != 0
    where prefix_mask[a] = { d : d < a }.
    """
    n = len(order)
    if n <= 2:
        return True

    # Bitset of neighbors of each vertex (by vertex id).
    nb = [0] * n
    for v in range(n):
        bits = 0
        for w in adj[v]:
            bits |= 1 << w
        nb[v] = bits

    # Bitsets over positions: for each position a,
    # S_a = positions c > a with order[a] adjacent to order[c]
    # T_a = positions b > a with order[a] NOT adjacent to order[b]
    # Build by scanning positions from the back.
    # pos_of_vertex[v] = position of v in the ordering.
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    # For each vertex v, bitset of positions of its neighbors.
    pos_nb = [0] * n
    for v in range(n):
        bits = 0
        for w in adj[v]:
            bits |= 1 << pos[w]
        pos_nb[v] = bits

    # allpos = (1 << n) - 1
    for a in range(n):
        va = order[a]
        # positions > a
        gt = ((1 << n) - 1) ^ ((1 << (a + 1)) - 1)
        S = pos_nb[va] & gt          # c > a, ac in E
        T = gt ^ S                   # b > a, ab not in E
        if T == 0:
            continue
        prefix = (1 << a) - 1        # d < a
        # For each b in T: need (N(b) & ~S) & prefix != 0
        # ~S restricted to positions: complement within all positions.
        notS = ((1 << n) - 1) ^ S
        t = T
        while t:
            lb = t & (-t)
            b = lb.bit_length() - 1
            vb = order[b]
            if (pos_nb[vb] & notS & prefix) == 0:
                return False
            t ^= lb
    return True


def _recompute(graph):
    adj = _adj_lists(graph)
    order = _lexbfs(adj)
    return {'ordering': order, 'adj': adj}


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['adj'][v].add(u)
    if _is_valid_lexbfs(state['ordering'], state['adj']):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['adj'][v].discard(u)
    if _is_valid_lexbfs(state['ordering'], state['adj']):
        return state
    return _recompute(graph)
