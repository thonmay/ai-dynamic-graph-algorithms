"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

Strategy: maintain a genuine DFS forest (parent, discover, finish) of the
current graph.  After each update, check whether the forest is still a valid
DFS forest of the new graph (Lemma 1: a spanning search tree is a DFS tree
iff it has no forward-cross edges, i.e. no edge u->v with
discover[u] < discover[v] and v not a descendant of u).  If it is valid,
return the state unchanged (O(n^2) check, no recompute).  If not, recompute
the DFS forest from scratch (O(n^2)).

This is correct for all updates; the cheap path is taken whenever the update
does not invalidate the forest (e.g. adding a back/forward edge, deleting a
non-tree edge, or an update that does not create a forward-cross edge).
"""


def _dfs(graph):
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

    dfs(0)
    return parent, discover, finish


def _is_valid(graph, parent, discover, finish):
    """Check the forest is a DFS forest of graph (Lemma 1).

    Conditions:
    1. parent pointers form a tree over the reachable set, each parent is a
       real in-neighbor discovered before its child.
    2. No forward-cross edge: for every edge u->v between reachable vertices
       with discover[u] < discover[v], v must be a descendant of u.
    """
    n = len(graph)
    for u in range(n):
        if discover[u] == -1:
            continue
        for v in range(n):
            if not graph[u][v]:
                continue
            if discover[v] == -1:
                # edge from reachable u to unreachable v: v should have been
                # discovered, so the forest is not spanning -> invalid.
                return False
            if discover[u] < discover[v]:
                # v must be a descendant of u
                if not (discover[u] < discover[v] and finish[v] < finish[u]):
                    return False
    # verify parent consistency on reachable vertices
    for v in range(n):
        if discover[v] == -1:
            if parent[v] is not None:
                return False
            continue
        p = parent[v]
        if p is None:
            if v != 0:
                return False
            continue
        if not graph[p][v]:
            return False
        if discover[p] >= discover[v]:
            return False
        if not (discover[p] < discover[v] and finish[v] < finish[p]):
            return False
    return True


def init(graph):
    parent, discover, finish = _dfs(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def insert_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid(graph, parent, discover, finish):
        return state
    parent, discover, finish = _dfs(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def delete_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid(graph, parent, discover, finish):
        return state
    parent, discover, finish = _dfs(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}
