"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Strategy: maintain a genuine DFS forest (parent, discover, finish).
- Insertion: if the new edge is a forward-cross edge w.r.t. the current
  forest, re-run DFS from scratch (rare, but always correct).
- Deletion: if the deleted edge is not a tree edge, the forest stays valid.
  If it is a tree edge, re-run DFS from scratch.

Re-running DFS from scratch is O(n^2) in the matrix representation, which is
the same as the offline algorithm; the dynamic checks avoid it in the common
case.
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


def _is_ancestor(u, v, discover, finish):
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def _is_forward_cross(u, v, discover, finish):
    # edge u->v is a forward-cross edge iff u discovered before v and
    # neither is an ancestor of the other.
    if discover[u] == -1 or discover[v] == -1:
        return False
    if discover[u] < discover[v]:
        return not _is_ancestor(u, v, discover, finish)
    return False


def _is_valid_forest_after_insert(u, v, parent, discover, finish):
    # After inserting edge u->v, the only new violation is the edge itself.
    # (Reachability only grows, so previously-reachable vertices stay
    # discovered; previously-unreachable vertices stay unreachable.)
    return not _is_forward_cross(u, v, discover, finish)


def init(graph):
    parent, discover, finish = _dfs(graph)
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
    if not _is_valid_forest_after_insert(u, v, parent, discover, finish):
        parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if parent[v] == u:
        parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
