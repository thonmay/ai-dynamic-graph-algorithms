"""Dynamic DFS forest from root 0 under single edge insertions/deletions.

Strategy (derived from the parent's interval re-search, with the parent's
two bugs fixed):

- init: full DFS from root 0, recording parent, discover, finish with one
  shared counter (discover 0..n-1, finish n..2n-1).
- insert_edge(u, v):
    * If v is unreachable: if u is reachable, extend the forest by DFS from
      v over the previously-unreachable vertices (starting after the last
      finish time), then renumber the whole reachable set so the numbering
      is contiguous.  (Parent bug fixed: the parent returned without
      renumbering, leaving a gap between the old finish times and the new
      discover times.)
    * If v is a descendant of u, or discover[v] < discover[u]: the old order
      stays valid, no change.
    * Otherwise (forward-cross edge): re-run DFS from u over the subgraph
      induced by vertices with discover >= discover[u].  The re-search
      discovers exactly the same vertex set (reachability from u is
      unchanged by adding one edge), so the numbering stays contiguous and
      no renumbering is needed.
- delete_edge(u, v):
    * If v is unreachable or parent[v] != u: no change.
    * Otherwise: re-run DFS from u over the subgraph induced by vertices
      with discover >= discover[u]; vertices no longer reachable get
      discover=-1.  Then renumber the whole reachable set to fix gaps.

Correctness argument for the interval re-search:
- Insertion: adding u->v with discover[u] < discover[v] and v not a
  descendant of u.  Any vertex w with discover[w] < discover[u] has no
  outgoing edge to a vertex in [discover[u], ...] that was previously
  undiscovered (otherwise w would have discovered it), and the new edge
  starts at u, so the prefix [0, discover[u]) is untouched and remains a
  valid DFS prefix.  The re-search from u over the suffix reproduces a
  genuine DFS of the suffix subgraph, and edges from the prefix into the
  suffix can only point at u (the first suffix vertex), which is the
  re-search root, so the combined order is a valid DFS of the whole graph.
- Deletion: removing a tree edge u->v (v a tree child of u) can only
  reduce reachability within the suffix [discover[u], ...]; the prefix is
  untouched.  The re-search from u over the suffix gives a valid DFS of
  the suffix of the new graph; renumbering restores contiguity.
"""


def _full_dfs(graph, n):
    """Full DFS from root 0.  Returns state dict."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    t = 0
    stack = [[0, 0]]
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
                stack[-1][1] = ci
                stack.append([w, 0])
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
    stack = [[root, 0]]
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
                stack[-1][1] = ci
                stack.append([w, 0])
                advanced = True
                break
        if not advanced:
            finish[v] = t
            t += 1
            stack.pop()
    return parent, discover, finish, t


def _renumber(parent, discover, finish, n):
    """Renumber all reachable vertices to a contiguous DFS numbering.

    Preserves the DFS tree structure (parent pointers) and the relative
    order of discover times.  Recomputes finish times via post-order so
    that finish[v] > finish[c] for every tree child c of v.
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

    # v unreachable: the new edge u->v may make v (and everything reachable
    # from v) newly reachable.
    if discover[v] == -1:
        if discover[u] == -1:
            # u unreachable: v stays unreachable, no effect
            return state
        # u reachable but v not: extend the forest by DFS from v over the
        # previously-unreachable vertices, starting after the last finish
        # time so existing intervals stay valid.
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
        # Renumber the whole reachable set so discover/finish are
        # contiguous (the extension started after a gap).
        parent, discover, finish = _renumber(parent, discover, finish, n)
        return {'parent': parent, 'discover': discover, 'finish': finish}

    # v is a descendant of u: forward edge, fine
    if discover[u] < discover[v] and finish[v] < finish[u]:
        return state
    # v discovered before u: back/cross edge, fine
    if discover[v] < discover[u]:
        return state
    # discover[u] < discover[v] and v not a descendant of u: forward-cross
    # edge.  Re-search from u over the suffix; the vertex set is unchanged,
    # so the numbering stays contiguous.
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
    # v is a tree child of u: re-search from u over the suffix.
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
