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
  * insert_edge (u,v):
      - if v already reachable: the new edge is a non-tree edge of the
        existing forest; the forest stays a valid DFS forest, no work.
      - if v unreachable and u reachable: the new edge makes v (and
        vertices reachable from v among the previously-unreachable set)
        newly reachable.  We run a DFS from v over the unreachable
        vertices, then splice the resulting subtree into u's interval by
        shifting the times of u's existing descendants.
  * delete_edge (u,v):
      - if v is not a tree child of u: the forest is unchanged.
      - if v is a tree child of u: check whether the subtree rooted at v
        is still reachable from the root without the edge u->v.  If yes,
        the forest is still valid.  If no, recompute from scratch.
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


def _subtree_reachable_without(graph, u, v):
    """Check whether v is reachable from root 0 in the current graph
    without using the edge u->v.  BFS from root."""
    n = len(graph)
    seen = [False] * n
    seen[0] = True
    queue = [0]
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        row = graph[x]
        for y in range(n):
            if not row[y]:
                continue
            if x == u and y == v:
                continue  # the deleted tree edge
            if not seen[y]:
                seen[y] = True
                if y == v:
                    return True
                queue.append(y)
    return False


def init(graph):
    return _state(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # If v is already reachable, the new edge is a non-tree edge;
    # the forest remains a valid DFS forest.
    if discover[v] != -1:
        return state

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

    shift = local_counter[0]
    du = discover[u]
    fu = finish[u]

    # Shift all proper descendants of u (discover in (du, fu)) by `shift`.
    for w in range(n):
        if discover[w] != -1 and du < discover[w] < fu:
            discover[w] += shift
            finish[w] += shift

    # u's finish time extends by `shift`.
    finish[u] = fu + shift

    # Assign the subtree's times: local time t maps to du + 1 + t.
    for w in visited:
        discover[w] = du + 1 + local_discover[w]
        finish[w] = du + 1 + local_finish[w]
        if w == v:
            parent[w] = u
        else:
            parent[w] = local_parent[w]

    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    n = len(graph)

    # If v is not a tree child of u, the forest is unchanged.
    if parent[v] != u:
        return state

    # v is a tree child of u.  Check if the subtree rooted at v is still
    # reachable from the root without the edge u->v.
    if _subtree_reachable_without(graph, u, v):
        return state

    # The subtree is disconnected; recompute from scratch.
    return _state(graph)
