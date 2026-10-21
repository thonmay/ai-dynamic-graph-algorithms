"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

- init: full DFS, store parent/discover/finish plus per-vertex adjacency sets.
- insert_edge: if the new edge is a forward-cross edge w.r.t. the current
  DFS order (disc[u] < disc[v] and v not a descendant of u), recompute the
  whole DFS. Otherwise the forest stays valid (no change).
- delete_edge: if the deleted edge is not a tree edge, the forest stays
  valid (no change). If it is a tree edge u->v, re-run DFS from root 0 with
  "fixed" vertices (finished, non-ancestor of v) fast-forwarded,
  renumbering only the affected region.
"""


def _dfs_full(graph):
    n = len(graph)
    parent = [None] * n
    disc = [-1] * n
    fin = [-1] * n
    clock = [0]

    def rec(u):
        disc[u] = clock[0]
        clock[0] += 1
        for v in range(n):
            if graph[u][v] and disc[v] == -1:
                parent[v] = u
                rec(v)
        fin[u] = clock[0]
        clock[0] += 1

    for s in range(n):
        if disc[s] == -1:
            rec(s)
    return parent, disc, fin


def _build_adj(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    return adj


def init(graph):
    n = len(graph)
    parent, disc, fin = _dfs_full(graph)
    return {
        'parent': parent,
        'discover': disc,
        'finish': fin,
        'adj': _build_adj(graph),
        'n': n,
    }


def _recompute(graph, state):
    n = state['n']
    parent, disc, fin = _dfs_full(graph)
    state['parent'] = parent
    state['discover'] = disc
    state['finish'] = fin
    state['adj'] = _build_adj(graph)
    return state


def _is_ancestor(disc, fin, a, b):
    return disc[a] <= disc[b] and fin[b] <= fin[a]


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    disc, fin = state['discover'], state['finish']
    if disc[u] < disc[v] and not _is_ancestor(disc, fin, u, v):
        return _recompute(graph, state)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    if state['parent'][v] != u:
        return state
    return _reattach(state, v)


def _reattach(state, v):
    """Tree edge parent[v]->v was deleted. Re-run DFS from root 0 with
    fixed-vertex fast-forwarding.

    Fixed vertices: finished in old DFS AND not an ancestor of v (and not v
    itself). They keep their old disc/fin and are treated as already
    visited. All other vertices (ancestors of v, v, and the old subtree of
    v) are renumbered.

    Renumbering: a single counter. Fixed vertices occupy their old numbers.
    When the counter reaches a fixed vertex's old disc, it jumps to that
    vertex's old fin.
    """
    n = state['n']
    old_parent = state['parent']
    old_disc = state['discover']
    old_fin = state['finish']
    adj = state['adj']

    # identify ancestors of v (including v)
    anc = set()
    x = v
    while x is not None:
        anc.add(x)
        x = old_parent[x]

    # fixed = finished, not ancestor of v
    fixed = [False] * n
    for w in range(n):
        if w not in anc and old_fin[w] != -1:
            fixed[w] = True

    # fixed vertices sorted by old disc; each occupies [old_disc, old_fin)
    fixed_sorted = sorted([w for w in range(n) if fixed[w]], key=lambda w: old_disc[w])
    fixed_disc_map = {old_disc[w]: old_fin[w] for w in fixed_sorted}

    # new DFS from root 0
    new_parent = [None] * n
    new_disc = [0] * n
    new_fin = [0] * n
    visited = [False] * n
    for w in range(n):
        if fixed[w]:
            visited[w] = True
            new_disc[w] = old_disc[w]
            new_fin[w] = old_fin[w]

    clock = [0]

    def advance_clock():
        """Advance clock past any fixed vertex whose old disc == clock."""
        while clock[0] in fixed_disc_map:
            clock[0] = fixed_disc_map[clock[0]]

    # iterative DFS
    root = 0
    if not visited[root]:
        visited[root] = True
        new_disc[root] = clock[0]
        clock[0] += 1
        advance_clock()
        stack = [(root, 0)]
        while stack:
            u, ni = stack[-1]
            advanced = False
            while ni < n:
                w = ni
                ni += 1
                if w == u:
                    continue
                if w not in adj[u]:
                    continue
                if visited[w]:
                    continue
                # discover w
                visited[w] = True
                new_parent[w] = u
                new_disc[w] = clock[0]
                clock[0] += 1
                advance_clock()
                stack[-1] = (u, ni)
                stack.append((w, 0))
                advanced = True
                break
            if not advanced:
                # finish u
                new_fin[u] = clock[0]
                clock[0] += 1
                advance_clock()
                stack.pop()

    # handle unreachable vertices (disc was -1 in old DFS)
    for w in range(n):
        if not visited[w]:
            new_parent[w] = None
            new_disc[w] = clock[0]
            clock[0] += 1
            advance_clock()
            new_fin[w] = clock[0]
            clock[0] += 1
            advance_clock()

    state['parent'] = new_parent
    state['discover'] = new_disc
    state['finish'] = new_fin
    return state
