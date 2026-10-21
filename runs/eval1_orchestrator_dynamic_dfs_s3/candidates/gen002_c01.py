"""Dynamic DFS forest maintenance for a directed graph, root = 0.

Strategy (correctness first, then cheaper than full recompute):

- Maintain parent[], discover[], finish[] for a genuine DFS forest of the
  current graph (single shared counter, root discovered first).
- On an edge update, first check whether the current forest is still a valid
  DFS forest of the updated graph (Lemma 1: a spanning tree is a DFS tree iff
  it has no forward-cross edge).  If it is valid, return the state unchanged.
- Otherwise, recompute the DFS forest from scratch.

The validity check is O(n^2) in the worst case (scanning all edges), which is
cheaper than a full DFS recompute (O(n^2) with adjacency matrix but with the
full bookkeeping), and avoids any recompute for the common case where the
update does not invalidate the forest.
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

    # Root is vertex 0; only vertices reachable from 0 are part of the forest.
    # Unreachable vertices keep discover/finish = -1 and parent = None.
    dfs(0)
    return parent, discover, finish


def _is_valid_dfs_forest(graph, parent, discover, finish):
    """Check that the state is a valid DFS forest of the current graph.

    Two conditions:
      1. The parent pointers must form a spanning tree of the reachable set:
         every reachable vertex except the root has a parent that is its
         in-neighbor in the current graph and is its ancestor in the forest.
      2. Lemma 1: no forward-cross edge.  For every edge u->v where both
         endpoints are reachable and discover[u] < discover[v], v must be a
         descendant of u: discover[u] < discover[v] < finish[v] < finish[u].
    """
    n = len(graph)
    for v in range(n):
        if discover[v] == -1:
            continue
        if v == 0:
            if parent[v] is not None:
                return False
            continue
        p = parent[v]
        if p is None:
            return False
        if discover[p] == -1:
            return False
        if not graph[p][v]:
            return False
        if not (discover[p] < discover[v] < finish[v] < finish[p]):
            return False
    for u in range(n):
        if discover[u] == -1:
            continue
        for v in range(n):
            if not graph[u][v]:
                continue
            if discover[v] == -1:
                continue
            if discover[u] < discover[v]:
                # v must be a strict descendant of u
                if not (discover[u] < discover[v] < finish[v] < finish[u]):
                    return False
    return True


def _make_state(graph):
    parent, discover, finish = _dfs_from_scratch(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def init(graph):
    return _make_state(graph)


def insert_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    u, v = edge
    # If the inserted edge's target was unreachable in the old state, the old
    # forest is no longer spanning of the new reachable set, so it cannot be
    # a valid DFS forest of the new graph.  Recompute.
    if discover[v] == -1:
        return _make_state(graph)
    if _is_valid_dfs_forest(graph, parent, discover, finish):
        return state
    return _make_state(graph)


def delete_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs_forest(graph, parent, discover, finish):
        return state
    return _make_state(graph)
