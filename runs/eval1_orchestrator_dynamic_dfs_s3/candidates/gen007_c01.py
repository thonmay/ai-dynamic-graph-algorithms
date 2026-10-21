"""Dynamic DFS forest maintenance (directed graph, fixed root 0).

Maintains a genuine DFS forest of the current graph under single edge
insertions and deletions.  The maintained state is a dict with:

  parent  : list, parent[v] is the DFS tree in-neighbor of v (None for root
            and for unreachable vertices)
  discover: list, DFS entry time of each vertex (shared counter, root = 0)
  finish  : list, DFS exit time of each vertex

Correctness invariant (Yang et al. Lemma 1): the tree is a DFS tree iff it
has no forward-cross edge, i.e. no edge u->v with discover[u] < discover[v]
and v not a descendant of u.

Strategy:
  * insert_edge (u,v):
      - if v is already reachable and the new edge is a back/forward edge
        (v is an ancestor of u, or v is a descendant of u), the forest
        stays a valid DFS forest, no work.
      - otherwise recompute from scratch.
  * delete_edge (u,v):
      - if v is not a tree child of u: the forest is unchanged.
      - if v is a tree child of u: the old forest is invalid (parent[v]
        dangles), so recompute from scratch.
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

    # If v is already reachable, the new edge is a non-tree edge.  It is
    # harmless only if it does not create a forward-cross edge, i.e. only if
    # v is a descendant of u (discover[u] < discover[v] < finish[v] <
    # finish[u]) or v is an ancestor of u (discover[v] < discover[u] <
    # finish[u] < finish[v]) or u == v.  Otherwise the old forest is no
    # longer a DFS forest of the current graph, so recompute from scratch.
    if discover[v] != -1:
        if discover[u] != -1:
            if discover[u] < discover[v] and finish[v] < finish[u]:
                # v is a proper descendant of u: forward edge, fine.
                return state
            if discover[v] < discover[u] and finish[u] < finish[v]:
                # v is a proper ancestor of u: back edge, fine.
                return state
            if u == v:
                # self-loop, fine.
                return state
        return _state(graph)

    # v is unreachable.  The new edge only matters if u is reachable.
    if discover[u] == -1:
        return state

    # v is unreachable and u is reachable: the new edge makes v (and
    # vertices reachable from v among the previously-unreachable set)
    # newly reachable.  Recompute from scratch.
    return _state(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']

    # If v is not a tree child of u, the forest is unchanged.
    if parent[v] != u:
        return state

    # v is a tree child of u: the deleted edge was a tree edge, so
    # parent[v] = u is now a dangling pointer and the old forest is
    # invalid.  Recompute from scratch.
    return _state(graph)
