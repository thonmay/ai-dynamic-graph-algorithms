"""Dynamic DFS forest maintenance (directed, root 0).

Strategy: maintain a genuine DFS forest of the current graph.  On each
update, check whether the current forest is still a valid DFS forest of
the new graph (Lemma 1: a spanning tree is a DFS tree iff it has no
forward-cross edges, plus the forest must span exactly the reachable set).
If it is valid, keep it (fast path).  If not, recompute the DFS forest
from scratch (correctness first).
"""


def _dfs(graph, n):
    """Iterative DFS from root 0. Returns (parent, discover, finish)."""
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    time = [0]
    # stack of (vertex, next_child_index)
    stack = []
    discover[0] = 0
    time[0] = 1
    stack.append((0, 0))
    while stack:
        u, ci = stack[-1]
        advanced = False
        row = graph[u]
        while ci < n:
            v = ci
            ci += 1
            if row[v] and discover[v] == -1:
                parent[v] = u
                discover[v] = time[0]
                time[0] += 1
                stack[-1] = (u, ci)
                stack.append((v, 0))
                advanced = True
                break
        if not advanced:
            finish[u] = time[0]
            time[0] += 1
            stack.pop()
    return parent, discover, finish


def _is_valid(graph, parent, discover, finish, n):
    """Check the forest is a DFS forest of graph (no forward-cross edges)."""
    for u in range(n):
        if discover[u] == -1:
            continue
        row = graph[u]
        for v in range(n):
            if not row[v]:
                continue
            if discover[v] == -1:
                # edge to unreachable vertex: fine (v not in forest)
                continue
            if discover[u] < discover[v]:
                # v must be a descendant of u
                if not (discover[u] < discover[v] < finish[v] < finish[u]):
                    return False
    # parent pointers must be actual edges of the current graph
    for v in range(n):
        if discover[v] != -1 and v != 0:
            p = parent[v]
            if p is None or not graph[p][v]:
                return False
    # spanning check: reachable set in graph must equal forest vertex set
    seen = [False] * n
    stack = [0]
    seen[0] = True
    while stack:
        u = stack.pop()
        for v in range(n):
            if graph[u][v] and not seen[v]:
                seen[v] = True
                stack.append(v)
    for v in range(n):
        if seen[v] != (discover[v] != -1):
            return False
    return True


def init(graph):
    n = len(graph)
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
        'n': n,
    }


def _maybe_recompute(graph, state):
    n = state['n']
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid(graph, parent, discover, finish, n):
        return state
    parent, discover, finish = _dfs(graph, n)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
        'n': n,
    }


def insert_edge(graph, edge, state):
    return _maybe_recompute(graph, state)


def delete_edge(graph, edge, state):
    return _maybe_recompute(graph, state)
