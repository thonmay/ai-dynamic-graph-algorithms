"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

Strategy: maintain a genuine DFS forest (parent, discover, finish) of the
current graph.  On each update, check whether the current forest is still a
valid DFS forest of the new graph (Yang et al. Lemma 1: a spanning search
tree is a DFS tree iff it has no forward-cross edges).  If it is valid, keep
it.  Otherwise recompute the DFS from scratch.
"""


def _dfs_recompute(graph):
    """Run a standard iterative DFS from vertex 0 and return (parent, discover, finish)."""
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    # Iterative DFS with explicit stack to avoid recursion limits.
    # Stack entries: [vertex, next_child_index]
    discover[0] = counter[0]
    counter[0] += 1
    stack = [[0, 0]]

    while stack:
        v, idx = stack[-1]
        # Find the next unvisited neighbor starting from idx
        found = False
        for w in range(idx, n):
            if graph[v][w] and discover[w] == -1:
                # Tree edge v -> w
                parent[w] = v
                discover[w] = counter[0]
                counter[0] += 1
                stack[-1][1] = w + 1  # resume after w next time
                stack.append([w, 0])
                found = True
                break
        if not found:
            # All neighbors processed; finish v
            finish[v] = counter[0]
            counter[0] += 1
            stack.pop()

    return parent, discover, finish


def _is_valid_dfs_forest(graph, parent, discover, finish):
    """Check whether (parent, discover, finish) is a valid DFS forest of graph.

    Conditions:
    1. parent[root] is None; for every reachable v != root, parent[v] is a
       tree in-neighbor discovered before v.
    2. For every edge u->v between reachable vertices with discover[u] <
       discover[v], v must be a descendant of u:
       discover[u] < discover[v] < finish[v] < finish[u].
    """
    n = len(graph)
    reachable = [d != -1 for d in discover]

    # Check parent pointers
    if parent[0] is not None:
        return False
    for v in range(n):
        if not reachable[v]:
            continue
        if v == 0:
            continue
        p = parent[v]
        if p is None:
            return False
        if not reachable[p]:
            return False
        if not graph[p][v]:
            return False
        if not (discover[p] < discover[v]):
            return False

    # Check no forward-cross edges:
    # For every edge u->v between reachable vertices with discover[u] < discover[v],
    # v must be a descendant of u (i.e., finish[v] < finish[u]).
    for u in range(n):
        if not reachable[u]:
            continue
        du = discover[u]
        fu = finish[u]
        for v in range(n):
            if not graph[u][v]:
                continue
            if not reachable[v]:
                continue
            dv = discover[v]
            if du < dv:
                # v must be a descendant of u: finish[v] < finish[u]
                if not (finish[v] < fu):
                    return False
    return True


def _make_state(graph):
    parent, discover, finish = _dfs_recompute(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    # If the target vertex was unreachable, it must now be reachable (since
    # u is reachable and u->v was just added).  The old forest cannot be valid.
    if state['discover'][v] == -1:
        return _make_state(graph)
    # Check if the current forest is still valid for the new graph.
    if _is_valid_dfs_forest(graph, state['parent'], state['discover'], state['finish']):
        return state
    # Otherwise recompute.
    return _make_state(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was a tree edge, the forest is definitely invalid.
    if state['parent'][v] == u and state['discover'][v] != -1:
        return _make_state(graph)
    # Otherwise check validity (deleting an edge can only remove forward-cross
    # edges, so the forest should still be valid, but verify to be safe).
    if _is_valid_dfs_forest(graph, state['parent'], state['discover'], state['finish']):
        return state
    return _make_state(graph)
