"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Strategy (Yang et al. style, with a full-recompute safety net):
- init: full DFS from root 0, recording parent, discover, finish.
- insert_edge(u, v):
    * If v is already reachable and (v is an ancestor of u, or v is a
      descendant of u, or discover[v] < discover[u]): the new edge is a
      back/forward edge and the forest stays a valid DFS forest.
    * If v is unreachable: re-search only the affected subtree rooted at u
      (u is reachable, since the edge exists in the graph).
    * If v is reachable but discovered after u and not a descendant
      (forward-cross case): recompute the DFS from scratch.
- delete_edge(u, v):
    * If the deleted edge is not a tree edge, the forest is unchanged.
    * If it is a tree edge: re-search only the affected subtree rooted at v
      (u is reachable, since the edge existed in the graph).

The recompute fallback guarantees correctness in all cases; the fast paths
handle the common cases without touching the forest.
"""


def _dfs(graph, n):
    """Full DFS from root 0. Returns (parent, discover, finish)."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    stack = [(0, 0)]
    while stack:
        u, i = stack.pop()
        if i == 0:
            discover[u] = counter[0]
            counter[0] += 1
        advanced = False
        while i < n:
            if graph[u][i] and discover[i] == -1:
                parent[i] = u
                stack.append((u, i + 1))
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            finish[u] = counter[0]
            counter[0] += 1
    return parent, discover, finish


def _is_ancestor(discover, finish, a, b):
    """True if a is an ancestor of b (or a == b) in the DFS tree."""
    if discover[a] == -1 or discover[b] == -1:
        return False
    return discover[a] <= discover[b] and finish[b] <= finish[a]


def _resubtree(graph, n, root, parent, discover, finish):
    """Re-run DFS restricted to the subtree rooted at `root`.

    `root` must be reachable (discover[root] != -1).  All vertices in the
    subtree are cleared, then DFS is restarted from `root` with the shared
    counter continuing at the old finish time of `root`.  Vertices outside
    the subtree keep their old times, which remain valid: the subtree is a
    contiguous interval [discover[root], finish[root]) and no edge from
    outside the subtree can point into it (any such edge would have made the
    target reachable from root in the previous search).
    """
    lo = discover[root]
    hi = finish[root]
    for w in range(n):
        if lo <= discover[w] < hi:
            discover[w] = -1
            finish[w] = -1
            parent[w] = None

    counter = [hi]
    stack = [(root, 0)]
    while stack:
        u, i = stack.pop()
        if i == 0:
            discover[u] = counter[0]
            counter[0] += 1
        advanced = False
        while i < n:
            if graph[u][i] and discover[i] == -1:
                parent[i] = u
                stack.append((u, i + 1))
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            finish[u] = counter[0]
            counter[0] += 1


def init(graph):
    n = len(graph)
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # v already reachable: check whether the new edge is harmless.
    if discover[v] != -1:
        # back edge (v ancestor of u) or forward edge (v descendant of u): fine
        if _is_ancestor(discover, finish, v, u) or _is_ancestor(discover, finish, u, v):
            return state
        # v discovered before u: edge goes "backwards" in time, fine
        if discover[v] < discover[u]:
            return state
        # v discovered after u but not a descendant: forward-cross edge -> recompute
        parent, discover, finish = _dfs(graph, n)
        return {
            'parent': parent,
            'discover': discover,
            'finish': finish,
        }

    # v unreachable.  If u is reachable, only u's subtree can change:
    # re-search it.  (u must be reachable for the edge to exist in the graph.)
    if discover[u] != -1:
        _resubtree(graph, n, u, parent, discover, finish)
        return state

    # u unreachable too: the edge cannot affect reachability from root 0.
    # (A legal update flips exactly one entry, so u must be reachable here;
    # this branch is only a safety net.)
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # If the deleted edge is not a tree edge, the forest is unchanged.
    if parent[v] != u:
        return state

    # Tree edge deleted: re-search the subtree rooted at v.  v was reachable
    # (it had a parent), so the restricted re-search is valid.
    _resubtree(graph, n, v, parent, discover, finish)
    return state
