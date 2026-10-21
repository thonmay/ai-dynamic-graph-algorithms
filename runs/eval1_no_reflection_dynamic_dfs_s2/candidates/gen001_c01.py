"""Dynamic DFS forest maintenance (directed, root 0).

Strategy: maintain a genuine DFS forest (parent, discover, finish) of the
current graph.  On an edge update we first check whether the current forest
is still a valid DFS forest of the new graph (Yang et al. Lemma 1: a search
tree is a DFS tree iff it has no forward-cross edges).  If it is valid, we
return the state unchanged (O(1) work).  Otherwise we recompute the DFS
forest from scratch.

The DFS visits all vertices: starting from root 0, then any undiscovered
vertex in increasing order, so every vertex gets a discover/finish time.
"""


def _dfs_from_scratch(graph):
    """Compute a DFS forest of `graph` from root 0 (then other roots).

    Returns (parent, discover, finish) where parent is a list with
    parent[root] = None, and discover/finish are lists of ints from a
    shared counter.
    """
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [0] * n
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

    for start in range(n):
        if discover[start] == -1:
            dfs(start)

    return parent, discover, finish


def _is_valid_dfs_forest(graph, parent, discover, finish):
    """Check whether (parent, discover, finish) is a valid DFS forest of
    `graph` rooted at 0.

    A search tree is a DFS tree iff it has no forward-cross edges:
    for every edge u->v with discover[u] < discover[v], v must be a
    descendant of u, i.e.
    discover[u] < discover[v] < finish[v] < finish[u].

    Returns True if valid, False otherwise.
    """
    n = len(graph)
    for u in range(n):
        for v in range(n):
            if not graph[u][v]:
                continue
            if discover[u] < discover[v]:
                # v must be a descendant of u
                if not (discover[v] < finish[v] < finish[u]):
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
    # A deletion can only invalidate the forest if the deleted edge was a
    # tree edge (i.e. parent[v] == u for edge (u, v)).  If it was not a
    # tree edge, the forest is unchanged and still valid.
    u, v = edge
    if parent[v] != u:
        return state
    # The deleted edge was a tree edge; recompute from scratch.
    parent, discover, finish = _dfs_from_scratch(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
