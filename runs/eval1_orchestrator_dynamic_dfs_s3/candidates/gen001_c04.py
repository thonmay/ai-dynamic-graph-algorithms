"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Maintains a genuine DFS forest of the current graph under single edge
insertions and deletions.  The maintained state is a dict with:

  parent  : list, parent[v] is the DFS tree in-neighbor of v (None for root
            and for unreachable vertices)
  discover: list, DFS entry time of each vertex (shared counter, root = 0)
  finish  : list, DFS exit time of each vertex

Correctness invariant (Yang et al. Lemma 1): the tree is a DFS tree iff it has
no forward-cross edge, i.e. no edge u->v with discover[u] < discover[v] and v
not a descendant of u.  After every update we verify this invariant and, if
it is violated, recompute the forest from scratch.  The recompute is a plain
iterative DFS over the current adjacency matrix.

This is a correct baseline: every update is O(n^2) in the worst case (the
invariant check is O(n^2) over all edges, and a recompute is O(n^2)).  The
invariant check is the cheap fast path: most updates leave the forest valid.
"""


def _dfs_from_scratch(graph):
    """Run a standard iterative DFS from root 0 and return (parent, discover, finish)."""
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    # Iterative DFS with explicit stack of (vertex, iterator over neighbors).
    # We simulate the recursive DFS exactly: discover on first visit, finish
    # after all descendants are done.
    root = 0
    if n == 0:
        return parent, discover, finish

    # Only vertex 0 is the root of the DFS forest; other vertices are visited
    # only if reachable from 0.
    stack = []
    # discover root
    discover[root] = 0
    counter[0] = 1
    # neighbors to explore for root
    stack.append([root, 0])  # [vertex, next neighbor index to try]

    while stack:
        v, ni = stack[-1]
        # find next unvisited neighbor
        found = False
        while ni < n:
            if graph[v][ni] and discover[ni] == -1:
                # descend
                discover[ni] = counter[0]
                counter[0] += 1
                parent[ni] = v
                stack[-1][1] = ni + 1
                stack.append([ni, 0])
                found = True
                break
            ni += 1
        if not found:
            # finish v
            finish[v] = counter[0]
            counter[0] += 1
            stack.pop()

    return parent, discover, finish


def _is_valid_dfs(graph, parent, discover, finish):
    """Check the Yang et al. invariant: no forward-cross edge.

    For every edge u->v where both are reachable (discover != -1):
      if discover[u] < discover[v], then v must be a descendant of u,
      i.e. discover[u] < discover[v] < finish[v] < finish[u].
    Also check parent consistency: parent[v] must be a tree in-neighbor
    discovered before v, and parent[root] is None.
    """
    n = len(graph)
    # parent consistency
    for v in range(n):
        if discover[v] == -1:
            # unreachable: parent must be None
            if parent[v] is not None:
                return False
            continue
        p = parent[v]
        if v == 0:
            if p is not None:
                return False
            continue
        if p is None:
            return False
        if not graph[p][v]:
            return False
        if discover[p] >= discover[v]:
            return False
        # p must be an ancestor of v
        if not (discover[p] < discover[v] < finish[v] < finish[p]):
            return False
    # forward-cross edge check
    for u in range(n):
        if discover[u] == -1:
            continue
        for v in range(n):
            if not graph[u][v]:
                continue
            if discover[v] == -1:
                # edge from a reachable vertex to an unreachable one:
                # the target should have been discovered, so invalid
                return False
            if discover[u] < discover[v]:
                # v must be a descendant of u
                if not (discover[v] < finish[v] < finish[u]):
                    return False
    return True


def _state(graph):
    parent, discover, finish = _dfs_from_scratch(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def init(graph):
    return _state(graph)


def insert_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs(graph, parent, discover, finish):
        return state
    return _state(graph)


def delete_edge(graph, edge, state):
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if _is_valid_dfs(graph, parent, discover, finish):
        return state
    return _state(graph)
