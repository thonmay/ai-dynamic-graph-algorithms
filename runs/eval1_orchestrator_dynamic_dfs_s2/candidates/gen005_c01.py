"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

- init: full DFS, store parent/discover/finish plus per-vertex adjacency sets.
- insert_edge: if the new edge is a forward-cross edge w.r.t. the current
  DFS order (disc[u] < disc[v] and v not a descendant of u), recompute the
  whole DFS. Otherwise the forest stays valid (no change).
- delete_edge: if the deleted edge is not a tree edge, the forest stays
  valid (no change). If it is a tree edge u->v, re-run a full DFS from
  root 0 over the current adjacency (unreachable vertices get
  discover/finish = -1, parent = None).
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
    """Tree edge parent[v]->v was deleted. Re-run a full DFS from root 0
    over the current adjacency. Unreachable vertices get
    discover/finish = -1 and parent = None.
    """
    n = state['n']
    adj = state['adj']

    new_parent = [None] * n
    new_disc = [-1] * n
    new_fin = [-1] * n
    visited = [False] * n

    clock = [0]
    root = 0
    visited[root] = True
    new_disc[root] = clock[0]
    clock[0] += 1
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
            stack[-1] = (u, ni)
            stack.append((w, 0))
            advanced = True
            break
        if not advanced:
            # finish u
            new_fin[u] = clock[0]
            clock[0] += 1
            stack.pop()

    state['parent'] = new_parent
    state['discover'] = new_disc
    state['finish'] = new_fin
    return state
