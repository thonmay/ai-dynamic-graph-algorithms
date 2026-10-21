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

    def visit(u):
        discover[u] = counter[0]
        counter[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                visit(v)
        finish[u] = counter[0]
        counter[0] += 1

    if n > 0:
        visit(0)
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
        # v discovered after u but not a descendant: forward-cross edge -> recompute
        # fall through

    # v unreachable, or forward-cross case: recompute
    parent, discover, finish = _dfs(graph, n)
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
