"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Strategy:
- Maintain parent, discover, finish.
- On insertion: if the new edge is a forward-cross edge w.r.t. the current
  DFS order, re-run DFS from the source of that edge.
- On deletion: if the deleted edge is a tree edge, re-run DFS from its child.
- Re-running DFS from a vertex v re-discovers v's subtree (and possibly more,
  if edges reach outside it) and renumbers the tail of the DFS order.
"""


def _adj(graph, u, n):
    return sorted(i for i in range(n) if graph[u][i])


def _dfs_from(graph, start, parent, discover, finish, n):
    """Re-run DFS from `start` (already discovered, discover[start] = d0).

    Clears start's old subtree, re-searches from start, then renumbers the
    tail of the old order (vertices discovered after the old subtree).
    """
    d0 = discover[start]
    f0 = finish[start]
    subtree = [x for x in range(n) if discover[x] is not None
               and discover[x] >= d0 and finish[x] <= f0]
    tail = [x for x in range(n) if discover[x] is not None
            and discover[x] > f0]
    tail_span = {x: finish[x] - discover[x] for x in tail}

    for x in subtree:
        parent[x] = None
        discover[x] = None
        finish[x] = None

    counter = d0
    stack = [(start, iter(_adj(graph, start, n)))]
    discover[start] = counter
    counter += 1
    while stack:
        u, it = stack[-1]
        advanced = False
        for v in it:
            if discover[v] is None:
                parent[v] = u
                discover[v] = counter
                counter += 1
                stack.append((v, iter(_adj(graph, v, n))))
                advanced = True
                break
        if not advanced:
            finish[u] = counter
            counter += 1
            stack.pop()

    for x in tail:
        discover[x] = counter
        counter += 1
    for x in tail:
        finish[x] = discover[x] + tail_span[x]


def _dfs_full(graph, n):
    """Full DFS from root 0. Returns (parent, discover, finish)."""
    parent = [None] * n
    discover = [None] * n
    finish = [None] * n
    counter = 0
    if n > 0:
        stack = [(0, iter(_adj(graph, 0, n)))]
        discover[0] = counter
        counter += 1
        while stack:
            u, it = stack[-1]
            advanced = False
            for v in it:
                if discover[v] is None:
                    parent[v] = u
                    discover[v] = counter
                    counter += 1
                    stack.append((v, iter(_adj(graph, v, n))))
                    advanced = True
                    break
            if not advanced:
                finish[u] = counter
                counter += 1
                stack.pop()
    return parent, discover, finish


def _is_ancestor(u, v, discover, finish):
    if discover[u] is None or discover[v] is None:
        return False
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def _is_forward_cross(u, v, discover, finish):
    if discover[u] is None or discover[v] is None:
        return False
    if u == v:
        return False
    return discover[u] < discover[v] and not _is_ancestor(u, v, discover, finish)


def init(graph):
    n = len(graph)
    parent, discover, finish = _dfs_full(graph, n)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    # Case 1: v was unreachable and is now reachable via u -> re-search from u.
    if discover[v] is None and discover[u] is not None:
        _dfs_from(graph, u, parent, discover, finish, n)
    # Case 2: new edge is a forward-cross edge -> re-search from u.
    elif _is_forward_cross(u, v, discover, finish):
        _dfs_from(graph, u, parent, discover, finish, n)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    if discover[v] is not None and parent[v] == u:
        _dfs_from(graph, v, parent, discover, finish, n)
    return {'parent': parent, 'discover': discover, 'finish': finish}
