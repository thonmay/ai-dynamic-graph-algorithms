"""Dynamic DFS forest maintenance (directed graph, root 0).

Strategy:
- init: full iterative DFS from root 0, recording parent, discover, finish.
- insert_edge(u, v):
    * If v is already a descendant of u (or u == v): the new edge is a
      forward/back edge, the forest stays valid -> no change.
    * If u is unreachable: no change.
    * If v is unreachable: v becomes a child of u (tree edge); renumber
      the tail of the time line.
    * If v is an ancestor of u: back edge -> no change.
    * Otherwise the new edge is a forward-cross edge: re-run DFS restricted
      to the subtree of u (u's interval), renumbering that interval in
      place.  This is always a valid DFS of the whole graph: the subtree
      of u is closed under outgoing edges to reachable vertices (any
      reachable vertex outside u's interval is either an ancestor of u or
      in a finished sibling subtree, and no edge from inside the subtree
      can point to a finished vertex that is not an ancestor).
- delete_edge(u, v):
    * If v is not a descendant of u: the edge was not a tree edge -> no
      change.
    * Otherwise the tree edge is gone: the affected region is the subtree
      of v.  Re-run DFS from u over the region (subtree of u minus the
      subtree of v), with the old order of the region as the tie-breaker
      for adjacency.  Any vertex of the old subtree of v that is not
      reached is unreachable in the current graph (it had no incoming
      edge from outside its subtree, and the only tree edge from outside
      was the deleted one).  Renumber the region in place.
"""


def _dfs_region(graph, start, region, order):
    """Iterative DFS of graph restricted to `region` (set of vertices),
    starting at `start`, using `order` as the adjacency tie-breaker.

    Returns (parent, discover, finish) dicts for the reached vertices.
    """
    n = len(graph)
    pos = {v: i for i, v in enumerate(order)}
    parent = {start: None}
    discover = {}
    finish = {}
    clock = 0
    stack = [(start, iter(sorted((w for w in range(n)
                                   if graph[start][w] and w in region),
                                  key=lambda w: pos[w])))]
    discover[start] = clock
    clock += 1
    while stack:
        u, it = stack[-1]
        advanced = False
        for w in it:
            if w not in discover:
                parent[w] = u
                discover[w] = clock
                clock += 1
                stack.append((w, iter(sorted((x for x in range(n)
                                              if graph[w][x] and x in region),
                                            key=lambda x: pos[x]))))
                advanced = True
                break
        if not advanced:
            finish[u] = clock
            clock += 1
            stack.pop()
    return parent, discover, finish


def _make_state(n, parent, discover, finish):
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
        'n': n,
    }


def init(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    if n == 0:
        return _make_state(n, parent, discover, finish)
    clock = 0
    stack = [(0, iter(range(n)))]
    discover[0] = clock
    clock += 1
    while stack:
        u, it = stack[-1]
        advanced = False
        for w in it:
            if discover[w] == -1:
                parent[w] = u
                discover[w] = clock
                clock += 1
                stack.append((w, iter(range(n))))
                advanced = True
                break
        if not advanced:
            finish[u] = clock
            clock += 1
            stack.pop()
    return _make_state(n, parent, discover, finish)


def _is_descendant(discover, finish, u, v):
    """True if v is a strict descendant of u (both reachable)."""
    return (discover[u] >= 0 and discover[v] >= 0
            and discover[u] < discover[v] < finish[v] < finish[u])


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    if discover[u] == -1:
        # u unreachable: v was unreachable too (edge just added, v could
        # only become reachable via u, but u is unreachable) -> no change.
        return state
    if discover[v] == -1:
        # v was unreachable: it becomes reachable as a child of u.  The
        # new edge is a tree edge; the rest of the forest is untouched.
        # Renumber the tail of the time line (all times >= finish[u])
        # to make room for v's interval.
        for w in range(n):
            if discover[w] >= 0 and discover[w] >= finish[u]:
                discover[w] += 2
                finish[w] += 2
        parent[v] = u
        discover[v] = finish[u] - 1
        finish[v] = finish[u]
        finish[u] += 2
        return state
    if _is_descendant(discover, finish, v, u):
        # back edge: forest stays valid.
        return state
    if u == v or _is_descendant(discover, finish, u, v):
        # forward or back edge: forest stays valid.
        return state

    # forward-cross edge: re-search the subtree of u.
    d0, f0 = discover[u], finish[u]
    region = [w for w in range(n)
              if discover[w] >= 0 and d0 <= discover[w] < f0]
    order = sorted(region, key=lambda w: discover[w])
    p, d, f = _dfs_region(graph, u, set(region), order)
    t0 = d[u]
    for w in region:
        if w in d:
            parent[w] = p[w]
            discover[w] = d[w] - t0
            finish[w] = f[w] - t0
        else:
            parent[w] = None
            discover[w] = -1
            finish[w] = -1
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    if not _is_descendant(discover, finish, u, v):
        # not a tree edge (or u unreachable): forest stays valid.
        return state

    # tree edge deleted: re-search the region = subtree(u) minus subtree(v).
    d0, f0 = discover[u], finish[u]
    dv0, fv0 = discover[v], finish[v]
    region = [w for w in range(n)
              if discover[w] >= 0 and d0 <= discover[w] < f0
              and not (dv0 <= discover[w] < fv0)]
    order = sorted(region, key=lambda w: discover[w])
    p, d, f = _dfs_region(graph, u, set(region), order)
    t0 = d[u]
    for w in region:
        if w in d:
            parent[w] = p[w]
            discover[w] = d[w] - t0
            finish[w] = f[w] - t0
        else:
            parent[w] = None
            discover[w] = -1
            finish[w] = -1
    # vertices of the old subtree of v that are not reached are unreachable
    # now (they had no incoming edge from outside their subtree).
    for w in range(n):
        if dv0 <= discover[w] < fv0 and discover[w] != -1:
            parent[w] = None
            discover[w] = -1
            finish[w] = -1
    return state
