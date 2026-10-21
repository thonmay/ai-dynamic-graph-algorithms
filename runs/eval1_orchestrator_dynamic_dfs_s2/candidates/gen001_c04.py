"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

Maintains a genuine DFS forest (parent, discover, finish) of the current
directed graph.  Updates are handled locally:

- Insertion u->v: if v is already discovered before u, or v is a descendant
  of u, the forest stays valid (new edge is a back/forward edge).  Otherwise
  the new edge is a forward-cross edge: re-search the subtree of u with the
  new edge present, renumbering that interval.
- Deletion u->v: if it was not a tree edge, nothing changes.  Otherwise the
  subtree of v is detached; re-search the subtree of u (with the edge gone)
  to reattach it, renumbering that interval.

Both cases only touch the subtree rooted at u, so the work is proportional to
the affected interval, not the whole graph.
"""


def _dfs_from(u, graph, parent, discover, finish, counter):
    """Iterative DFS starting at u (already discovered, discover[u] set).

    Fills parent/discover/finish for the subtree reachable from u, using the
    shared counter.  Returns the counter value after finishing u.
    """
    n = len(graph)
    stack = [[u, 0]]
    while stack:
        x, ci = stack[-1]
        advanced = False
        while ci < n:
            if graph[x][ci] and discover[ci] == -1:
                parent[ci] = x
                discover[ci] = counter[0]
                counter[0] += 1
                stack[-1][1] = ci + 1
                stack.append([ci, 0])
                advanced = True
                break
            ci += 1
        if not advanced:
            finish[x] = counter[0]
            counter[0] += 1
            stack.pop()
    return counter[0]


def _is_ancestor(u, v, discover, finish):
    return discover[u] < discover[v] and finish[v] < finish[u]


def _make_state(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]
    discover[0] = 0
    counter[0] = 1
    _dfs_from(0, graph, parent, discover, finish, counter)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def _resubtree(u, graph, parent, discover, finish):
    """Re-run DFS on the subtree rooted at u (u stays discovered at its
    current time); renumbers the whole interval [discover[u], finish[u])."""
    n = len(graph)
    base = discover[u]
    # collect subtree vertices
    sub = [v for v in range(n) if discover[v] != -1 and _is_ancestor(u, v, discover, finish)]
    # reset them
    for v in sub:
        discover[v] = -1
        finish[v] = -1
        parent[v] = None
    # re-discover u at the same time
    discover[u] = base
    counter = [base + 1]
    _dfs_from(u, graph, parent, discover, finish, counter)
    # renumber the whole interval so times are contiguous
    # (DFS from u visits exactly the vertices reachable from u, which is the
    #  same set as the old subtree, so the interval length is unchanged)
    old_len = finish[u] - base
    # build mapping: old order of discovery -> new
    # vertices in sub, sorted by new discover
    ordered = sorted(sub, key=lambda v: discover[v])
    for i, v in enumerate(ordered):
        discover[v] = base + i
    # finish times: recompute by sorting by new finish
    ordered_f = sorted(sub, key=lambda v: finish[v])
    for i, v in enumerate(ordered_f):
        finish[v] = base + old_len - len(ordered_f) + i + 1


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if discover[v] == -1:
        # v unreachable: no effect on the forest
        return state
    if discover[v] < discover[u]:
        # new edge is a back edge: forest stays valid
        return state
    if _is_ancestor(u, v, discover, finish):
        # new edge is a forward edge: forest stays valid
        return state
    # forward-cross edge: re-search subtree of u
    _resubtree(u, graph, parent, discover, finish)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if parent[v] != u:
        # not a tree edge: forest stays valid
        return state
    # tree edge deleted: re-search subtree of u
    _resubtree(u, graph, parent, discover, finish)
    return state
