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
      - if v is unreachable and u is reachable: v (and everything reachable
        from v among the previously-unreachable vertices) becomes newly
        reachable.  Re-search only the newly-reachable set S, attaching it
        as a new child subtree of u right after u's existing subtree
        (at position f[u]), shifting all later times by |S|.
      - otherwise (v reachable but the edge is a forward-cross edge) the old
        forest is no longer a DFS forest of the current graph: recompute
        from scratch.
  * delete_edge (u,v):
      - if v is not a tree child of u: the forest is unchanged.
      - if v is a tree child of u: the old forest is invalid (parent[v]
        dangles).  Recompute from scratch.
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


def _shift_times(state, lo, delta):
    """Add delta to discover/finish of every vertex with discover >= lo."""
    d, f = state['discover'], state['finish']
    for x in range(len(d)):
        if d[x] >= lo:
            d[x] += delta
            f[x] += delta


def _search_newly_reachable(graph, state, u, v):
    """Insert case: v was unreachable, u is reachable, edge u->v added.

    Re-search the set S of vertices reachable from v in the current graph
    (all of S was previously unreachable, since only one edge was added and
    it is u->v).  Attach S to u as a new child subtree at position f[u]
    (right after u's existing subtree), shifting all later times by |S|.
    """
    n = len(graph)
    d, f = state['discover'], state['finish']
    parent = state['parent']

    # --- find S: DFS from v over vertices with discover == -1 ---
    S = []
    stack = [v]
    d[v] = -2  # mark as in-S (sentinel, distinct from -1)
    while stack:
        x = stack.pop()
        S.append(x)
        row = graph[x]
        for y in range(n):
            if row[y] and d[y] == -1:
                d[y] = -2
                stack.append(y)

    # Restore d for S vertices to -1 (they were marked -2)
    for x in S:
        d[x] = -1

    # --- insert at position f[u] (right after u's existing subtree) ---
    insert_pos = f[u]
    s_size = len(S)

    # Shift all vertices with discover >= insert_pos by s_size
    _shift_times(state, insert_pos, s_size)

    # Update u's finish time: u's subtree now includes S, so u finishes later
    f[u] += s_size

    # --- assign times to S: DFS from v, starting at insert_pos ---
    S_set = set(S)
    t = insert_pos
    d[v] = t
    t += 1
    parent[v] = u
    stack = [[v, 0]]
    while stack:
        x, ni = stack[-1]
        found = False
        while ni < n:
            if graph[x][ni] and d[ni] == -1 and ni in S_set:
                d[ni] = t
                t += 1
                parent[ni] = x
                stack[-1][1] = ni + 1
                stack.append([ni, 0])
                found = True
                break
            ni += 1
        if not found:
            f[x] = t
            t += 1
            stack.pop()

    return state


def init(graph):
    return _state(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    discover = state['discover']
    finish = state['finish']

    # If v is already reachable, the new edge is a non-tree edge.  It is
    # harmless only if it does not create a forward-cross edge, i.e. only
    # if v is a descendant of u (discover[u] < discover[v] < finish[v] <
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
    # newly reachable.  Do a local re-search.
    return _search_newly_reachable(graph, state, u, v)


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
