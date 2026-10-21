"""Dynamic DFS forest from a fixed root (vertex 0) under edge updates.

Maintains a genuine DFS forest (parent pointers + discover/finish times from
one shared counter) of the current directed graph.

Correctness strategy:
  * init: full iterative DFS.
  * insert_edge: if the new edge is a forward-cross edge w.r.t. the current
    forest (source discovered before target, target not a descendant of
    source), or if the target was unreachable (becomes reachable), recompute
    the whole forest.  Otherwise the forest stays valid.
  * delete_edge: if the deleted edge is not a tree edge, the forest is
    unchanged and still valid.  If it is a tree edge, recompute the whole
    forest (correctness first; the fast path covers most updates).

State dict keys:
  parent, discover, finish : required result fields
  n, adj, tree_children, subtree, tin, tout : auxiliary
"""


def _dfs_full(n, adj):
    """Full iterative DFS from root 0. Returns (parent, discover, finish,
    tree_children, subtree, tin, tout)."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    tree_children = [[] for _ in range(n)]
    subtree = [[] for _ in range(n)]
    tin = [0] * n
    tout = [0] * n
    t = 0
    stack = [(0, 0)]
    discover[0] = 0
    t = 1
    while stack:
        u, i = stack[-1]
        advanced = False
        while i < len(adj[u]):
            v = adj[u][i]
            i += 1
            if discover[v] == -1:
                discover[v] = t
                t += 1
                parent[v] = u
                tree_children[u].append(v)
                subtree[u].append(v)
                stack[-1] = (u, i)
                stack.append((v, 0))
                advanced = True
                break
        if not advanced:
            stack.pop()
            finish[u] = t
            t += 1
            tin[u] = discover[u]
            tout[u] = finish[u]
            if stack:
                pu = stack[-1][0]
                subtree[pu].append(u)
    return parent, discover, finish, tree_children, subtree, tin, tout


def _is_descendant(u, v, tin, tout):
    """True if v is a proper descendant of u (u discovered, v inside u's
    interval)."""
    return tin[u] < tin[v] and tout[v] <= tout[u]


def _rebuild(n, adj):
    return _dfs_full(n, adj)


def _make_state(n, adj, parent, discover, finish, tree_children, subtree,
                 tin, tout):
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
        'n': n,
        'adj': adj,
        'tree_children': tree_children,
        'subtree': subtree,
        'tin': tin,
        'tout': tout,
    }


def init(graph):
    n = len(graph)
    adj = [list(row) for row in graph]
    parent, discover, finish, tc, sub, tin, tout = _dfs_full(n, adj)
    st = _make_state(n, adj, parent, discover, finish, tc, sub, tin, tout)
    st['_dbg_init'] = (n, [list(r) for r in graph], list(parent), list(discover), list(finish))
    return st


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = [list(row) for row in graph]
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    tin = state['tin']
    tout = state['tout']

    # If the source is unreachable, the new edge cannot affect the forest.
    if discover[u] == -1:
        st = _make_state(n, adj, parent, discover, finish,
                         state['tree_children'], state['subtree'], tin, tout)
        st['_dbg_ins'] = ('src_unreach', u, v, list(discover))
        return st

    # If the target is unreachable, it becomes reachable: recompute the
    # forest (the new vertex must be discovered in DFS order, and the
    # discovery order of existing vertices may change).
    if discover[v] == -1:
        parent, discover, finish, tc, sub, tin, tout = _rebuild(n, adj)
        return _make_state(n, adj, parent, discover, finish, tc, sub, tin, tout)

    # New edge is a forward-cross edge iff u discovered before v and v is
    # not a descendant of u.  That invalidates the DFS forest.
    if discover[u] < discover[v] and not _is_descendant(u, v, tin, tout):
        parent, discover, finish, tc, sub, tin, tout = _rebuild(n, adj)
        return _make_state(n, adj, parent, discover, finish, tc, sub, tin, tout)

    # Otherwise the forest remains a valid DFS forest.
    return _make_state(n, adj, parent, discover, finish,
                       state['tree_children'], state['subtree'], tin, tout)


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = [list(row) for row in graph]
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    tin = state['tin']
    tout = state['tout']
    tree_children = state['tree_children']
    subtree = state['subtree']

    # Not a tree edge: forest unchanged and still valid.
    if parent[v] != u:
        return _make_state(n, adj, parent, discover, finish,
                           tree_children, subtree, tin, tout)

    # Tree edge u->v deleted: recompute the full forest.
    parent, discover, finish, tc, sub, tin, tout = _rebuild(n, adj)
    return _make_state(n, adj, parent, discover, finish, tc, sub, tin, tout)
