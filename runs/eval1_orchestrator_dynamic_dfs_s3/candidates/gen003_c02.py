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
      - if v already reachable: the new edge is a non-tree edge of the
        existing forest.  It is harmless only if it does not create a
        forward-cross edge, i.e. only if v is a descendant of u
        (discover[u] < discover[v] < finish[v] < finish[u]).  Otherwise the
        old forest is no longer a DFS forest of the current graph, so
        recompute from scratch.
      - if v unreachable and u reachable: the new edge makes v (and
        vertices reachable from v among the previously-unreachable set)
        newly reachable.  We run a DFS from v over the unreachable
        vertices, then splice the resulting subtree into u's interval by
        shifting the times of u's existing descendants.
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
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # If v is already reachable, the new edge is a non-tree edge.  It is
    # harmless only if it does not create a forward-cross edge, i.e. only if
    # v is a descendant of u (discover[u] < discover[v] < finish[v] <
    # finish[u]).  Otherwise the old forest is no longer a DFS forest of the
    # current graph, so recompute from scratch.
    if discover[v] != -1:
        if discover[u] != -1 and discover[u] < discover[v] and finish[v] < finish[u]:
            return state
        return _state(graph)

    # v is unreachable.  The new edge only matters if u is reachable.
    if discover[u] == -1:
        return state

    # Run a DFS from v over the currently-unreachable vertices.
    visited = set()
    visited.add(v)
    local_parent = {}
    local_discover = {}
    local_finish = {}
    local_counter = [0]
    local_discover[v] = 0
    local_counter[0] = 1
    stack = [[v, 0]]

    while stack:
        x, ni = stack[-1]
        found = False
        while ni < n:
            if graph[x][ni] and discover[ni] == -1 and ni not in visited:
                visited.add(ni)
                local_discover[ni] = local_counter[0]
                local_counter[0] += 1
                local_parent[ni] = x
                stack[-1][1] = ni + 1
                stack.append([ni, 0])
                found = True
                break
            ni += 1
        if not found:
            local_finish[x] = local_counter[0]
            local_counter[0] += 1
            stack.pop()

    # The new subtree occupies the interval (du, fu) and u's own finish
    # time is preserved.  Shift all proper descendants of u (discover in
    # (du, fu)) by `shift` to make room, then place the new subtree right
    # after u's discovery.
    shift = local_counter[0]
    du = discover[u]
    fu = finish[u]

    for w in range(n):
        if discover[w] != -1 and du < discover[w] < fu:
            discover[w] += shift
            finish[w] += shift

    # Assign the subtree's times: local time t maps to du + 1 + t.
    for w in visited:
        discover[w] = du + 1 + local_discover[w]
        finish[w] = du + 1 + local_finish[w]
        if w == v:
            parent[w] = u
        else:
            parent[w] = local_parent[w]

    # u's finish time extends by `shift` (the new subtree is explored
    # before u's old descendants, so u finishes later).
    finish[u] = fu + shift

    # Every ancestor of u (discover < du, finish > fu) also finishes later
    # by `shift`.
    for w in range(n):
        if discover[w] != -1 and discover[w] < du and finish[w] > fu:
            finish[w] += shift

    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    n = len(graph)

    # If v is not a tree child of u, the forest is unchanged.
    if parent[v] != u:
        return state

    # v is a tree child of u: the deleted edge was a tree edge, so
    # parent[v] = u is now a dangling pointer and the old forest is
    # invalid.  Recompute from scratch.
    return _state(graph)
