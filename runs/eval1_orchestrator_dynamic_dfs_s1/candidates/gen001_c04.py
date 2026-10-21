"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Strategy: maintain a genuine DFS forest (parent, discover, finish) of the
current graph.  On an update, check whether the current forest is still a
valid DFS forest of the new graph (Lemma 1: a spanning search tree is a DFS
tree iff it has no forward-cross edges).  If it is, keep it.  Otherwise
recompute the DFS from scratch.

This is correct for all updates; the recompute is bounded by the size of the
graph, and many updates (e.g. adding a back/forward edge, deleting a
non-tree edge) are handled in O(n) without a full search.
"""


def _dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    def rec(u):
        discover[u] = counter[0]
        counter[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                rec(v)
        finish[u] = counter[0]
        counter[0] += 1

    if n > 0:
        rec(0)
    return parent, discover, finish


def _is_valid_dfs(graph, parent, discover, finish, edge, inserted):
    """Check the forest is a DFS forest of graph (Lemma 1).

    `edge` is the (u, v) entry that was just flipped; `inserted` says whether
    it was added.  The check is incremental:

    - If an edge was inserted: the old forest was valid for the old graph, so
      only the new edge can create a forward-cross edge.  Check it.
    - If an edge was deleted: the old forest was valid for the old graph.
      Deleting an edge cannot create a forward-cross edge, so the only way
      validity can break is if some vertex becomes unreachable.  Check
      reachability closure.
    """
    n = len(graph)
    u, v = edge
    if inserted:
        # The new edge can (a) make previously unreachable vertices reachable,
        # or (b) create a forward-cross edge.  Check both.
        if discover[u] != -1 and discover[v] == -1:
            # v becomes reachable; BFS from v in the new graph
            reach = [False] * n
            stack = [v]
            reach[v] = True
            while stack:
                x = stack.pop()
                for y in range(n):
                    if graph[x][y] and not reach[y]:
                        reach[y] = True
                        stack.append(y)
            for w in range(n):
                if reach[w] and discover[w] == -1:
                    return False
        if discover[u] != -1 and discover[v] != -1 and discover[u] < discover[v]:
            if not (discover[u] < discover[v] < finish[v] < finish[u]):
                return False
        return True
    # deletion: the old forest was valid for the old graph.  Deleting an edge
    # cannot create a forward-cross edge, so the only way validity can break
    # is if some vertex becomes unreachable.  Check reachability closure.
    reach = [False] * n
    if n > 0:
        stack = [0]
        reach[0] = True
        while stack:
            x = stack.pop()
            for y in range(n):
                if graph[x][y] and not reach[y]:
                    reach[y] = True
                    stack.append(y)
    for w in range(n):
        if reach[w] != (discover[w] != -1):
            return False
    return True


def init(graph):
    parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def insert_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs(graph, parent, discover, finish, edge, True):
        return state
    parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs(graph, parent, discover, finish, edge, False):
        return state
    parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
