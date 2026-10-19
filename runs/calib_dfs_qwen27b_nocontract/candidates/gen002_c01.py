"""Dynamic DFS forest maintenance for directed graphs, root = vertex 0.

State shape:
    {
      'n': int,
      'parent': list[int],   # parent[v] = p or -1 (root / unreachable)
      'disc': list[int],     # discovery times, 0 for undiscovered
      'fin': list[int],      # finish times, 0 for undiscovered
      'time': int,           # global DFS clock
    }

Correctness invariant: (parent, disc, fin) is a valid DFS forest of the
current graph rooted at 0, i.e. there exists a DFS run (with some legal
adjacency ordering) producing exactly these times and tree edges.  By
Yang et al.'s Lemma 1 this is equivalent to: the tree edges form a spanning
forest of the reachable set and there is no forward-cross edge.

Strategy (dynamic, no full recompute on most updates):
  * insert_edge(u, v):
      - if v already discovered: the new edge is a tree/forward/back/cross
        edge relative to the existing DFS order; a DFS forest is never
        invalidated by adding an edge whose target is already discovered
        (it can only become a forward or back edge, or a cross edge from a
        later-discovered vertex, all of which are legal).  No change.
      - if v undiscovered: v is unreachable from 0 before the update, so
        the new edge u->v (u reachable) makes v and everything reachable
        from v newly reachable.  We run a DFS from v over the current
        graph, restricted to vertices that are currently undiscovered,
        continuing the global clock.  This is exactly what a DFS run that
        had just finished u's subtree would do next, so the resulting
        times are consistent with a legal DFS order.
  * delete_edge(u, v):
      - if v is not a tree child of u: the forest is unchanged (the edge
        was a non-tree edge; removing it cannot break reachability of any
        vertex via the tree, and cannot create a forward-cross edge).
      - if v is a tree child of u: the subtree rooted at v may lose
        reachability.  We recompute the DFS restricted to the affected
        region: the subtree of v plus any currently-discovered vertices
        that are reachable from v's old subtree via non-tree edges,
        EXCLUDING u and all of u's ancestors (those remain reachable via
        the tree path from the root and must not be cleared).  We clear
        the whole affected set, then re-run DFS from u's other children
        (in old discovery order) over the current graph, restricted to
        the affected set, continuing the global clock.  Vertices that
        remain reachable get new (larger) times; the relative order of the
        unaffected part is preserved, and the new times are all larger
        than every unaffected vertex's times, so ancestor relations and
        the no-forward-cross-edge property are maintained.

The affected-set computation for deletion is the only nontrivial part;
it is a BFS/DFS over the current graph starting from the old subtree of v,
following only edges into currently-discovered vertices that are not
ancestors of u, which is O(n^2) worst case but touches only the affected
region in practice.
"""


def _dfs_from(start, graph, state, allowed):
    """Iterative DFS from `start` over `graph`, visiting only vertices in
    `allowed` (a set of vertex ids) that are not yet discovered,
    continuing state's global clock.  Updates parent/disc/fin in state.
    Returns None."""
    n = state['n']
    parent = state['parent']
    disc = state['disc']
    fin = state['fin']
    t = state['time']
    stack = [(start, 0)]
    disc[start] = t + 1
    t += 1
    while stack:
        v, i = stack[-1]
        advanced = False
        while i < n:
            if graph[v][i] and i in allowed and disc[i] == 0:
                stack[-1] = (v, i + 1)
                disc[i] = t + 1
                t += 1
                parent[i] = v
                stack.append((i, 0))
                advanced = True
                break
            i += 1
        if not advanced:
            stack.pop()
            fin[v] = t
            t += 1
    state['time'] = t


def init(graph):
    n = len(graph)
    parent = [-1] * n
    disc = [0] * n
    fin = [0] * n
    state = {'n': n, 'parent': parent, 'disc': disc, 'fin': fin, 'time': 0}
    if n > 0:
        _dfs_from(0, graph, state, set(range(n)))
    return state


def _subtree(v, state):
    """Return the set of vertices in the DFS subtree rooted at v
    (v must be discovered)."""
    parent = state['parent']
    out = set()
    stack = [v]
    while stack:
        x = stack.pop()
        out.add(x)
        for y in range(state['n']):
            if parent[y] == x:
                stack.append(y)
    return out


def _affected_set(root, u, graph, state):
    """For a deleted tree edge (u, root): the set of currently-discovered
    vertices that may lose reachability = the old subtree of root plus any
    discovered vertex reachable from that subtree via any edge, EXCLUDING
    u and all of u's ancestors (they stay reachable via the tree path)."""
    parent = state['parent']
    disc = state['disc']
    n = state['n']
    sub = _subtree(root, state)
    affected = set(sub)
    # Ancestors of u (including u itself) must never be cleared.
    ancestors = set()
    a = u
    while a != -1:
        ancestors.add(a)
        a = parent[a]
    # BFS from every vertex in the subtree, following edges into
    # discovered vertices not yet in affected and not ancestors of u.
    queue = list(sub)
    qi = 0
    while qi < len(queue):
        x = queue[qi]
        qi += 1
        row = graph[x]
        for y in range(n):
            if row[y] and disc[y] > 0 and y not in affected and y not in ancestors:
                affected.add(y)
                queue.append(y)
    return affected


def insert_edge(graph, edge, state):
    u, v = edge
    disc = state['disc']
    if disc[v] > 0:
        # target already discovered: adding the edge cannot invalidate the
        # DFS forest (it becomes a forward/back/cross edge, all legal).
        return state
    # v was unreachable; it (and what it reaches among the unreachable)
    # becomes reachable.  DFS from v over currently-undiscovered vertices.
    n = state['n']
    allowed = {x for x in range(n) if disc[x] == 0}
    if v not in allowed:
        return state
    state['parent'][v] = u
    _dfs_from(v, graph, state, allowed)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    disc = state['disc']
    if parent[v] != u:
        return state
    n = state['n']
    affected = _affected_set(v, u, graph, state)
    # capture old discovery order of u's other children in the affected
    # set before clearing; these are the entry points for the re-DFS.
    entries = [w for w in affected if parent[w] == u]
    entries.sort(key=lambda w: disc[w])
    # clear affected
    for x in affected:
        disc[x] = 0
        state['fin'][x] = 0
        parent[x] = -1
    # re-run DFS from each entry point (in old discovery order) over the
    # affected set, continuing the global clock.  Each entry point that
    # is still reachable from u gets re-discovered; the first one reached
    # becomes a child of u.
    for w in entries:
        if disc[w] == 0:
            parent[w] = u
            _dfs_from(w, graph, state, affected)
    return state
