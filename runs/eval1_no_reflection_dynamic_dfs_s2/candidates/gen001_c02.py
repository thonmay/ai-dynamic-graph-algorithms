"""Dynamic DFS forest from a fixed root (vertex 0) under edge insertions/deletions.

Approach:
- Maintain parent pointers, discovery/finish times (shared counter).
- On updates that provably don't affect the forest, do nothing.
- On updates that do affect the forest, recompute the full DFS.

Correctness:
- Insertion u->v does NOT affect the forest if:
  * u is unreachable (discover[u] == -1)
  * discover[v] < discover[u] (back/cross edge to earlier vertex)
  * v is a descendant of u (forward edge)
  Otherwise it may create a forward-cross edge or make v reachable.
- Deletion u->v does NOT affect the forest if:
  * v is unreachable
  * parent[v] != u (not a tree edge)
  Otherwise the subtree of v may lose connectivity.
"""


def _dfs_full(graph):
    """Run a full DFS from vertex 0. Returns (parent, discover, finish)."""
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n

    if n == 0:
        return parent, discover, finish

    counter = 0
    # Iterative DFS: stack of [vertex, next_child_idx]
    discover[0] = counter
    counter += 1
    stack = [[0, 0]]

    while stack:
        v, next_c = stack[-1]
        advanced = False
        while next_c < n:
            if graph[v][next_c] and discover[next_c] == -1:
                parent[next_c] = v
                discover[next_c] = counter
                counter += 1
                stack[-1][1] = next_c + 1
                stack.append([next_c, 0])
                advanced = True
                break
            next_c += 1
        if not advanced:
            finish[v] = counter
            counter += 1
            stack.pop()
            if stack:
                stack[-1][1] = next_c

    return parent, discover, finish


def _make_state(parent, discover, finish):
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def _is_descendant(u, v, discover, finish):
    """Check if v is a descendant of u (including u itself)."""
    if discover[u] == -1 or discover[v] == -1:
        return False
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def init(graph):
    parent, discover, finish = _dfs_full(graph)
    return _make_state(parent, discover, finish)


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    if discover[u] == -1:
        # u is unreachable, edge doesn't affect the forest
        return state

    if discover[v] == -1:
        # v is unreachable, becomes reachable. Need to recompute.
        parent, discover, finish = _dfs_full(graph)
        return _make_state(parent, discover, finish)

    if discover[v] < discover[u]:
        # Back/cross edge, no violation
        return state

    if _is_descendant(u, v, discover, finish):
        # Forward edge (v is descendant of u), no violation
        return state

    # Forward-cross edge violation: discover[u] < discover[v], v not
    # descendant of u. Need to recompute.
    parent, discover, finish = _dfs_full(graph)
    return _make_state(parent, discover, finish)


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']

    if discover[v] == -1:
        # v is unreachable, deletion doesn't affect the forest
        return state

    if parent[v] != u:
        # Not a tree edge, no effect on the forest
        return state

    # Tree edge deleted. v's subtree may lose connectivity.
    parent, discover, finish = _dfs_full(graph)
    return _make_state(parent, discover, finish)
