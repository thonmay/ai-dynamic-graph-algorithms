"""Dynamic DFS forest from a fixed root (vertex 0) under edge updates.

Strategy: maintain a genuine DFS forest (parent, discover, finish) of the
current graph.  On an update, first check whether the current forest is still
a valid DFS forest of the new graph (Lemma 1: a spanning tree is a DFS tree
iff it has no forward-cross edge).  If it is valid, return the state
unchanged.  Otherwise, recompute the DFS forest from scratch.

The validity check is O(n + m) in the worst case, so the update is O(n + m)
in the worst case, but avoids the full recompute whenever the forest
remains valid.
"""


def _dfs_from_scratch(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    def dfs(u):
        discover[u] = counter[0]
        counter[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                dfs(v)
        finish[u] = counter[0]
        counter[0] += 1

    # DFS from root 0 only (single-source DFS forest)
    dfs(0)
    return parent, discover, finish


def _is_valid_dfs_forest(graph, parent, discover, finish):
    """Check whether (parent, discover, finish) is a valid DFS forest of graph.

    Conditions:
    1. parent pointers form a tree rooted at 0 over reachable vertices.
    2. discover/finish times are consistent with the tree (intervals).
    3. No forward-cross edge: for every edge u->v between reachable vertices
       with discover[u] < discover[v], v must be a descendant of u.
    4. Every vertex reachable from 0 in the graph must be in the forest.
    5. The parent tree must span exactly the reachable set (no extra vertices).
    """
    n = len(graph)
    # Check interval consistency: for each tree edge u->v (parent[v]==u),
    # discover[u] < discover[v] < finish[v] < finish[u]
    for v in range(n):
        if discover[v] == -1:
            continue
        p = parent[v]
        if p is not None:
            if not (discover[p] < discover[v] < finish[v] < finish[p]):
                return False
    # Check no forward-cross edge
    for u in range(n):
        if discover[u] == -1:
            continue
        for v in range(n):
            if not graph[u][v]:
                continue
            if discover[v] == -1:
                # Edge to unreachable vertex: this would mean v should be
                # reachable, so the forest is invalid.
                return False
            if discover[u] < discover[v]:
                # v must be a descendant of u
                if not (discover[u] < discover[v] < finish[v] < finish[u]):
                    return False
    # Check that all vertices reachable from 0 in the graph are in the forest.
    visited = [False] * n
    stack = [0]
    visited[0] = True
    while stack:
        u = stack.pop()
        for v in range(n):
            if graph[u][v] and not visited[v]:
                visited[v] = True
                stack.append(v)
    for v in range(n):
        if visited[v] and discover[v] == -1:
            return False
    # Check that the parent tree spans exactly the reachable set.
    tree_count = sum(1 for v in range(n) if discover[v] != -1)
    reach_count = sum(1 for v in range(n) if visited[v])
    if tree_count != reach_count:
        return False
    # Check that the parent tree is connected (all reachable vertices are
    # connected to root 0 via parent pointers).
    if discover[0] == -1:
        return False
    # Build children list.
    children = [[] for _ in range(n)]
    for v in range(n):
        if discover[v] != -1 and parent[v] is not None:
            children[parent[v]].append(v)
    # BFS from 0 in the tree.
    tree_visited = [False] * n
    tree_visited[0] = True
    tstack = [0]
    while tstack:
        u = tstack.pop()
        for v in children[u]:
            if not tree_visited[v]:
                tree_visited[v] = True
                tstack.append(v)
    for v in range(n):
        if discover[v] != -1 and not tree_visited[v]:
            return False
    return True


def init(graph):
    parent, discover, finish = _dfs_from_scratch(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def insert_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs_forest(graph, parent, discover, finish):
        return state
    parent, discover, finish = _dfs_from_scratch(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs_forest(graph, parent, discover, finish):
        return state
    parent, discover, finish = _dfs_from_scratch(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
