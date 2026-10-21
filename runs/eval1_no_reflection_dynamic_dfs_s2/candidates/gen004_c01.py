"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Strategy:
- init: full DFS from root 0, recording parent, discover, finish.
- insert_edge(u, v):
    * If v is already reachable: the new edge is a back/forward/cross edge
      relative to the existing forest, all of which are legal in a DFS
      forest, so the state is unchanged.
    * If v is unreachable and u is reachable: v becomes reachable; recompute.
    * If both are unreachable: nothing changes.
- delete_edge(u, v):
    * If the deleted edge is not a tree edge, the forest is unchanged.
    * If it is a tree edge and v is no longer reachable: the remaining
      forest is still valid; no recompute needed.
    * If it is a tree edge and v is still reachable: recompute.

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

    # Tree edge deleted: the subtree rooted at v may still be reachable via
    # other edges.  Recompute only if v is still reachable in the new graph.
    n = len(graph)
    discover = state['discover']
    finish = state['finish']

    # BFS/DFS from root 0 in the new graph to see if v is reachable.
    # Only need to check reachability, not full DFS.
    seen = [False] * n
    stack = [0]
    seen[0] = True
    while stack:
        x = stack.pop()
        for y in range(n):
            if graph[x][y] and not seen[y]:
                seen[y] = True
                stack.append(y)

    if not seen[v]:
        # v and its subtree are now unreachable; the remaining forest is
        # still a valid DFS forest of the reachable part.
        return state

    # v is still reachable: recompute
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
