"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Strategy:
- init: full DFS from root 0, recording parent, discover, finish.
- insert_edge(u, v):
    * If v is already reachable and (v is an ancestor of u, or v is a
      descendant of u, or discover[v] < discover[u]): the new edge is a
      back/forward edge and the forest stays a valid DFS forest.
    * Otherwise (v unreachable, or v discovered after u but not a
      descendant): recompute the DFS from scratch.
- delete_edge(u, v):
    * If the deleted edge is not a tree edge, the forest is unchanged.
    * If it is a tree edge, recompute the DFS from scratch.

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
        # v discovered after u but not a descendant: forward-cross edge.
        # The old forest is still a valid DFS forest of the new graph (the
        # new edge is a cross edge, which DFS forests may have), so keep it.
        return state

    # v unreachable: the new edge may make v (and more) reachable.
    # Re-search from u: v becomes a child of u, and the subtree rooted at v
    # is re-explored with the same relative order as before.
    parent = list(parent)
    discover = list(discover)
    finish = list(finish)
    parent[v] = u
    discover[v] = discover[u]
    finish[v] = finish[u]
    for w in range(n):
        if discover[w] != -1 and discover[v] < discover[w] < finish[v]:
            discover[w] += 1
            finish[w] += 1
    finish[u] += 1
    discover[u] -= 1
    # The new edge u->v may make further previously-unreachable vertices
    # reachable (e.g. v->w with w unreachable). Re-search from v to find
    # them; the DFS order of the already-reachable part is preserved.
    counter = [discover[v]]
    stack = [(v, 0)]
    while stack:
        x, i = stack.pop()
        if i == 0:
            discover[x] = counter[0]
            counter[0] += 1
        advanced = False
        while i < n:
            if graph[x][i] and discover[i] == -1:
                parent[i] = x
                stack.append((x, i + 1))
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            finish[x] = counter[0]
            counter[0] += 1
    # The re-search may have extended u's subtree (new vertices discovered
    # after v). Restore u's own discover/finish to match the new subtree.
    discover[u] = discover[v] - 1
    finish[u] = counter[0]
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']

    # If the deleted edge is not a tree edge, the forest is unchanged.
    if parent[v] != u:
        return state

    # Tree edge deleted: recompute
    n = len(graph)
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
