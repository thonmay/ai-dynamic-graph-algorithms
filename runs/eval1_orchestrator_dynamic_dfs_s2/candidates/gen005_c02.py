"""Dynamic DFS forest maintenance (directed, root 0).

Strategy:
- init: full DFS from root 0, recording parent, discover, finish.
- insert_edge(u, v):
    * If u unreachable: no change.
    * If v unreachable: v becomes reachable via u -> recompute full DFS.
    * If v already reachable and (v is ancestor of u, or u is ancestor of v,
      or u == v): the new edge is a back/forward/self edge -> no change.
    * If discover[u] < discover[v] and v not descendant of u: forward-cross
      edge -> recompute full DFS.
    * Otherwise (cross edge with discover[v] < discover[u]): fine, no change.
- delete_edge(u, v):
    * If not a tree edge (parent[v] != u): no change.
    * If tree edge: recompute full DFS.

Correctness: any valid DFS order is accepted by the verifier.
"""


def _dfs_full(graph):
    n = len(graph)
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





def _is_ancestor(u, v, discover, finish):
    """Is u an ancestor of v (or u == v)?"""
    if discover[u] == -1 or discover[v] == -1:
        return False
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def init(graph):
    parent, discover, finish = _dfs_full(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # If the source is unreachable, nothing new becomes reachable
    if discover[u] == -1:
        return state

    # If the target is unreachable, it becomes reachable via u: recompute
    if discover[v] == -1:
        parent, discover, finish = _dfs_full(graph)
        return {'parent': parent, 'discover': discover, 'finish': finish}

    # Self-loop: no change
    if u == v:
        return state

    # If v is ancestor of u: back edge, no change
    if _is_ancestor(v, u, discover, finish):
        return state

    # If u is ancestor of v: forward edge, no change
    if _is_ancestor(u, v, discover, finish):
        return state

    # Neither is ancestor of the other.
    # If discover[u] < discover[v]: forward-cross edge -> invalidates DFS
    # If discover[v] < discover[u]: cross edge (finish[v] < discover[u]) -> fine
    if discover[u] < discover[v]:
        # Forward-cross edge: need to recompute
        parent, discover, finish = _dfs_full(graph)
        return {'parent': parent, 'discover': discover, 'finish': finish}

    # Cross edge (discover[v] < discover[u], finish[v] < discover[u]): fine
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    # If the edge is not a tree edge, no change
    if parent[v] != u:
        return state

    # Tree edge deleted: subtree rooted at v may become unreachable.
    # Recompute full DFS.
    parent, discover, finish = _dfs_full(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}
