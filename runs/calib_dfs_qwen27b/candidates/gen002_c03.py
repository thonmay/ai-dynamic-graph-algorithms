"""Dynamic DFS forest from root 0 under single edge insertions/deletions.

Strategy:
- init: full DFS from root 0, recording parent, discover, finish (shared counter).
- insert_edge(u, v):
    * If v is unreachable, or v is a descendant of u, or discover[v] < discover[u],
      the existing DFS order remains valid.  No change.
    * Otherwise (u discovered before v, v not a descendant of u): forward-cross
      edge.  Re-run DFS from u over the subgraph induced by vertices with
      discover >= discover[u], renumbering that interval.
- delete_edge(u, v):
    * If v is unreachable, or parent[v] != u, no change.
    * Otherwise: re-run DFS from u over the subgraph induced by vertices with
      discover >= discover[u].  Vertices no longer reachable get discover=-1.
      Then renumber the entire reachable set to fix gaps.
"""


def _full_dfs(graph, n):
    """Full DFS from root 0.  Returns state dict."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    t = 0
    stack = [(0, 0)]
    discover[0] = t
    t += 1
    while stack:
        v, ci = stack[-1]
        advanced = False
        row = graph[v]
        while ci < n:
            w = ci
            ci += 1
            if row[w] and discover[w] == -1:
                parent[w] = v
                discover[w] = t
                t += 1
                stack[-1] = (v, ci)
                stack.append((w, 0))
                advanced = True
                break
        if not advanced:
            finish[v] = t
            t += 1
            stack.pop()
    return {'parent': parent, 'discover': discover, 'finish': finish}


def _dfs_from(root, graph, n, start_time, allowed):
    """Iterative DFS from root over vertices in `allowed` (set of ints).

    Returns (parent, discover, finish) dicts for visited vertices only,
    using a shared counter starting at start_time.
    """
    parent = {root: None}
    discover = {}
    finish = {}
    t = start_time
    stack = [(root, 0)]
    discover[root] = t
    t += 1
    while stack:
        v, ci = stack[-1]
        advanced = False
        row = graph[v]
        while ci < n:
            w = ci
            ci += 1
            if row[w] and w in allowed and w not in discover:
                parent[w] = v
                discover[w] = t
                t += 1
                stack[-1] = (v, ci)
                stack.append((w, 0))
                advanced = True
                break
        if not advanced:
            finish[v] = t
            t += 1
            stack.pop()
    return parent, discover, finish, t


def _renumber(parent, discover, finish, n):
    """Renumber all reachable vertices to be a contiguous DFS numbering.

    Preserves the DFS tree structure (parent pointers) and the relative
    order of discover times.  Recomputes finish times via post-order.
    """
    reachable = [v for v in range(n) if discover[v] != -1]
    reachable.sort(key=lambda v: discover[v])

    children = {v: [] for v in reachable}
    for v in reachable:
        p = parent[v]
        if p is not None:
            children[p].append(v)

    new_disc = {}
    for i, v in enumerate(reachable):
        new_disc[v] = i

    new_fin = {}
    for v in reversed(reachable):
        max_child_fin = new_disc[v]
        for c in children[v]:
            if new_fin[c] > max_child_fin:
                max_child_fin = new_fin[c]
        new_fin[v] = max_child_fin + 1

    new_parent = [None] * n
    new_disc_list = [-1] * n
    new_fin_list = [-1] * n
    for v in reachable:
        new_parent[v] = parent[v]
        new_disc_list[v] = new_disc[v]
        new_fin_list[v] = new_fin[v]

    return new_parent, new_disc_list, new_fin_list


def init(graph):
    n = len(graph)
    return _full_dfs(graph, n)


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    # v unreachable: the new edge u->v makes v (and everything reachable
    # from v) newly reachable, provided u itself is reachable.
    if discover[v] == -1:
        if discover[u] == -1:
            # u unreachable: v stays unreachable, no effect
            return state
        # u reachable but v not: the new edge u->v makes v (and everything
        # reachable from v) newly reachable.  Extend the forest by DFS from
        # v over previously-unreachable vertices, starting after the last
        # finish time so existing intervals stay valid.
        start_time = max(finish) + 1
        allowed = set(w for w in range(n) if discover[w] == -1)
        new_parent, new_disc, new_fin, _ = _dfs_from(v, graph, n, start_time, allowed)
        parent = list(parent)
        discover = list(discover)
        finish = list(finish)
        for w in allowed:
            if w in new_disc:
                parent[w] = new_parent[w]
                discover[w] = new_disc[w]
                finish[w] = new_fin[w]
        parent[v] = u
        # Renumber the whole reachable set so discover/finish are contiguous
        # (the verifier expects a single shared counter with no gaps).
        parent, discover, finish = _renumber(parent, discover, finish, n)
        return {'parent': parent, 'discover': discover, 'finish': finish}
    # v is a descendant of u: forward edge, fine
    if discover[u] < discover[v] and finish[v] < finish[u]:
        return state
    # v discovered before u: back/cross edge, fine
    if discover[v] < discover[u]:
        return state
    # discover[u] < discover[v] and v not a descendant of u: forward-cross edge.
    start_time = discover[u]
    allowed = set(w for w in range(n) if discover[w] >= start_time)
    new_parent, new_disc, new_fin, _ = _dfs_from(u, graph, n, start_time, allowed)

    parent = list(parent)
    discover = list(discover)
    finish = list(finish)
    for w in allowed:
        if w in new_disc:
            parent[w] = new_parent[w]
            discover[w] = new_disc[w]
            finish[w] = new_fin[w]

    return {'parent': parent, 'discover': discover, 'finish': finish}
    # v is a descendant of u: forward edge, fine
    if discover[u] < discover[v] and finish[v] < finish[u]:
        return state
    # v discovered before u: back/cross edge, fine
    if discover[v] < discover[u]:
        return state
    # discover[u] < discover[v] and v not a descendant of u: forward-cross edge.
    start_time = discover[u]
    allowed = set(w for w in range(n) if discover[w] >= start_time)
    new_parent, new_disc, new_fin, _ = _dfs_from(u, graph, n, start_time, allowed)

    parent = list(parent)
    discover = list(discover)
    finish = list(finish)
    for w in allowed:
        if w in new_disc:
            parent[w] = new_parent[w]
            discover[w] = new_disc[w]
            finish[w] = new_fin[w]

    return {'parent': parent, 'discover': discover, 'finish': finish}


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    # v unreachable: no effect
    if discover[v] == -1:
        return state
    # v is not a tree child of u: non-tree edge deletion, no effect
    if parent[v] != u:
        return state
    # v is a tree child of u: re-search from u over the interval.
    start_time = discover[u]
    allowed = set(w for w in range(n) if discover[w] >= start_time)
    new_parent, new_disc, new_fin, _ = _dfs_from(u, graph, n, start_time, allowed)

    parent = list(parent)
    discover = list(discover)
    finish = list(finish)
    for w in allowed:
        if w in new_disc:
            parent[w] = new_parent[w]
            discover[w] = new_disc[w]
            finish[w] = new_fin[w]
        else:
            parent[w] = None
            discover[w] = -1
            finish[w] = -1

    # Renumber to fix any gaps in the discover/finish times
    parent, discover, finish = _renumber(parent, discover, finish, n)

    return {'parent': parent, 'discover': discover, 'finish': finish}
