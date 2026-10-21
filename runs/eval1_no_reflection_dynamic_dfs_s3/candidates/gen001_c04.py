"""Dynamic DFS forest from a fixed root (vertex 0) under edge insertions/deletions.

Strategy (correct-first, then cheaper):
- Maintain parent / discover / finish from a genuine DFS of the current graph.
- On an update, first test whether the existing forest is still a valid DFS
  forest of the new graph (Lemma 1: a spanning search tree is a DFS tree iff
  it has no forward-cross edge, i.e. an edge u->v with discover[u] <
  discover[v] and v not a descendant of u).
- If it is still valid, return the state unchanged (O(n) check, no recompute).
- Otherwise, recompute the DFS from scratch (worst case O(n^2)).

This is always correct: if the old forest is still a DFS forest of the new
graph, it is a legal answer; otherwise a fresh DFS is trivially legal.
"""


def _dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    clock = [0]

    def rec(u):
        discover[u] = clock[0]
        clock[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                rec(v)
        finish[u] = clock[0]
        clock[0] += 1

    rec(0)
    return parent, discover, finish


def _is_valid_dfs_forest(graph, parent, discover, finish):
    """Check the Lemma-1 condition: no forward-cross edge.

    For every edge u->v with discover[u] < discover[v], v must be a
    descendant of u: discover[u] < discover[v] < finish[v] < finish[u].
    Edges with discover[u] >= discover[v] (back edges) are fine.
    """
    n = len(graph)
    for u in range(n):
        du = discover[u]
        if du < 0:
            continue
        fu = finish[u]
        row = graph[u]
        for v in range(n):
            if row[v]:
                dv = discover[v]
                if dv > du:
                    # v discovered after u: v must be a descendant of u
                    # (forward edge is fine; only forward-cross is not).
                    if not (du < dv < finish[v] and dv < fu):
                        return False
    return True


def init(graph):
    parent, discover, finish = _dfs(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def insert_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs_forest(graph, parent, discover, finish):
        return state
    parent, discover, finish = _dfs(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def delete_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs_forest(graph, parent, discover, finish):
        return state
    parent, discover, finish = _dfs(graph)
    return {'parent': parent, 'discover': discover, 'finish': finish}
