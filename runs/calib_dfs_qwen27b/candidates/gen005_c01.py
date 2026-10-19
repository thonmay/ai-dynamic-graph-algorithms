"""Dynamic DFS forest from a fixed root (vertex 0) under edge insert/delete.

Strategy (Yang et al. style, with a correct fallback):
- Maintain a genuine DFS forest (parent, discover, finish) of the current
  graph.
- On an update, check whether the current forest is still a valid DFS forest
  of the new graph (Lemma 1: a spanning search tree is a DFS tree iff it has
  no forward-cross edges).  If it is valid, keep it.  If not, recompute the
  DFS from scratch (correct fallback).

This is correct for every update; the fast path avoids recomputation whenever
the old forest remains a valid DFS forest of the updated graph.
"""


def _dfs_from(graph, root):
    """Iterative DFS from root; returns (parent, discover, finish)."""
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    t = 0
    # stack of [vertex, next_child_index]
    stack = [[root, 0]]
    discover[root] = t
    t += 1
    while stack:
        u, i = stack[-1]
        advanced = False
        while i < n:
            if graph[u][i] and discover[i] == -1:
                parent[i] = u
                discover[i] = t
                t += 1
                stack[-1][1] = i + 1
                stack.append([i, 0])
                advanced = True
                break
            i += 1
        if not advanced:
            finish[u] = t
            t += 1
            stack.pop()
    return parent, discover, finish


def _is_valid_dfs(graph, parent, discover, finish):
    """Check the forest is a valid DFS forest of graph.

    Conditions:
    1. discover/finish form a proper DFS interval structure: exactly one
       root (vertex 0), every other discovered vertex has a unique parent
       whose interval strictly contains it, and every edge u->v with
       discover[u] < discover[v] has v as a descendant of u (no
       forward-cross edges).
    2. Every parent edge exists in the current graph.
    """
    n = len(graph)
    # 1. interval structure: each discovered vertex (except root) must have
    #    exactly one discovered vertex whose interval strictly contains it.
    for v in range(n):
        dv = discover[v]
        if dv == -1:
            if parent[v] is not None:
                return False
            continue
        if v == 0:
            if parent[v] is not None:
                return False
            continue
        p = parent[v]
        if p is None:
            return False
        if not graph[p][v]:
            return False
        dp = discover[p]
        if dp == -1:
            return False
        if not (dp < dv and dv < finish[v] and finish[v] < finish[p]):
            return False
        # uniqueness: no other vertex may strictly contain v
        for w in range(n):
            if w == p:
                continue
            dw = discover[w]
            if dw != -1 and dw < dv and dv < finish[v] and finish[v] < finish[w]:
                return False
    # 2. no forward-cross edges
    for u in range(n):
        du = discover[u]
        if du == -1:
            continue
        for v in range(n):
            if not graph[u][v]:
                continue
            dv = discover[v]
            if dv == -1:
                # edge to unreachable vertex: u reachable, v not -> v should
                # be reachable. Invalid.
                return False
            if du < dv:
                # v discovered after u: v must be a descendant of u
                if not (dv < finish[v] and finish[v] < finish[u]):
                    return False
    return True


def _make_state(graph):
    parent, discover, finish = _dfs_from(graph, 0)
    return {'parent': parent, 'discover': discover, 'finish': finish}


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    parent, discover, finish = state['parent'], state['discover'], state['finish']
    if _is_valid_dfs(graph, parent, discover, finish):
        return state
    return _make_state(graph)


def delete_edge(graph, edge, state):
    parent, discover, finish = state['parent'], state['discover'], state['finish']
    if _is_valid_dfs(graph, parent, discover, finish):
        return state
    return _make_state(graph)
