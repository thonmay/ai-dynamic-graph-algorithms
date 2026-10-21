"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Maintains a genuine DFS forest of the current graph under single edge
insertions and deletions.  The maintained state is a dict with:

  parent  : list, parent[v] is the DFS tree in-neighbor of v (None for root
            and for unreachable vertices)
  discover: list, DFS entry time of each vertex (shared counter, root = 0)
  finish  : list, DFS exit time of each vertex

Correctness invariant (Yang et al. Lemma 1): the tree is a DFS tree iff it has
no forward-cross edge, i.e. no edge u->v with discover[u] < discover[v] and v
not a descendant of u.

Strategy:
  * Insertion: if the new edge u->v is a back edge (v is an ancestor of u) or
    a forward edge (v is a proper descendant of u), the forest stays valid.
    Otherwise (cross edge, or v unreachable) we recompute from scratch.
  * Deletion: if the deleted edge is not a tree edge, the forest stays valid.
    If it is a tree edge, we recompute from scratch.

The recompute is a plain iterative DFS over the current adjacency matrix.
"""


def _dfs_from_scratch(graph):
    """Run a standard iterative DFS from root 0 and return (parent, discover, finish)."""
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    if n == 0:
        return parent, discover, finish

    root = 0
    discover[root] = 0
    counter[0] = 1
    stack = [[root, 0]]  # [vertex, next neighbor index to try]

    while stack:
        v, ni = stack[-1]
        found = False
        while ni < n:
            if graph[v][ni] and discover[ni] == -1:
                discover[ni] = counter[0]
                counter[0] += 1
                parent[ni] = v
                stack[-1][1] = ni + 1
                stack.append([ni, 0])
                found = True
                break
            ni += 1
        if not found:
            finish[v] = counter[0]
            counter[0] += 1
            stack.pop()

    return parent, discover, finish


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
    u, v = edge
    discover = state['discover']
    finish = state['finish']

    # If v is unreachable, the new edge may make it reachable -> recompute.
    if discover[v] == -1:
        return _state(graph)

    # Back edge: v is an ancestor of u (or v == u, self-loop).
    if discover[u] != -1 and discover[v] < discover[u] and finish[u] < finish[v]:
        return state
    if u == v:
        return state

    # Forward edge: v is a proper descendant of u.
    if discover[u] < discover[v] and finish[v] < finish[u]:
        return state

    # Otherwise the new edge is a cross edge (or u unreachable) -> recompute.
    return _state(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']

    # If the deleted edge is not a tree edge, the forest stays valid.
    if parent[v] != u or discover[v] == -1:
        return state

    # Tree edge deleted: the subtree rooted at v may become unreachable or
    # need re-parenting.  Recompute from scratch.
    return _state(graph)
