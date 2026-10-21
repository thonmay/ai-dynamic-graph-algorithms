"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Strategy: maintain a genuine DFS forest (parent, discover, finish) of the
current graph.  On an update, first check whether the current forest is
still a valid DFS forest of the new graph (no forward-cross edge).  If it
is, keep it.  Otherwise recompute the DFS forest from scratch.

This is correct for every update; the fast path avoids recomputation when
the update does not invalidate the forest.
"""


def _dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    for s in range(n):
        if discover[s] != -1:
            continue
        stack = [(s, 0)]
        discover[s] = counter[0]
        counter[0] += 1
        while stack:
            u, i = stack.pop()
            advanced = False
            while i < n:
                if graph[u][i] and discover[i] == -1:
                    parent[i] = u
                    discover[i] = counter[0]
                    counter[0] += 1
                    stack.append((u, i + 1))
                    stack.append((i, 0))
                    advanced = True
                    break
                i += 1
            if not advanced:
                finish[u] = counter[0]
                counter[0] += 1
    return parent, discover, finish


def _is_valid_dfs(graph, parent, discover, finish):
    n = len(graph)
    # parent edges must exist in the graph
    for v in range(n):
        p = parent[v]
        if p is not None:
            if discover[v] == -1 or discover[p] == -1:
                return False
            if not graph[p][v]:
                return False
            if not (discover[p] < discover[v] < finish[v] < finish[p]):
                return False
    for u in range(n):
        if discover[u] == -1:
            continue
        for v in range(n):
            if not graph[u][v]:
                continue
            if discover[v] == -1:
                continue
            if discover[u] < discover[v]:
                # v must be a descendant of u
                if not (discover[u] < discover[v] < finish[v] < finish[u]):
                    return False
    return True


def _make_state(graph):
    parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    if _is_valid_dfs(graph, state['parent'], state['discover'], state['finish']):
        return state
    return _make_state(graph)


def delete_edge(graph, edge, state):
    if _is_valid_dfs(graph, state['parent'], state['discover'], state['finish']):
        return state
    return _make_state(graph)
