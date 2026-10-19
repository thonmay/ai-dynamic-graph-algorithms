"""Dynamic BFS tree from fixed root 0 under directed edge updates.

State: dict with
  'distances' : dict vertex -> BFS distance from root, or -1 if unreachable
  'parent'    : dict vertex -> BFS tree parent, None for root and unreachable
  'n'         : number of vertices
  'tree'      : list of lists, tree children (outgoing tree edges)
  'in_tree'   : list of lists, incoming tree edges (children of v)
  'adj'       : list of sets, current out-neighborhood (kept in sync)
  'indeg'     : list of sets, current in-neighborhood (kept in sync)

Insertions: incremental - only affected vertices are revisited, and only if
the new edge strictly improves their distance.
Deletions: recompute BFS from scratch (simple, always correct).
"""


def _bfs(n, adj):
    dist = [-1] * n
    parent = [-1] * n
    tree = [[] for _ in range(n)]
    in_tree = [[] for _ in range(n)]
    dist[0] = 0
    q = [0]
    head = 0
    while head < len(q):
        u = q[head]
        head += 1
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                parent[v] = u
                tree[u].append(v)
                in_tree[v].append(u)
                q.append(v)
    return dist, parent, tree, in_tree


def _make_state(n, dist, parent, tree, in_tree, adj, indeg):
    return {
        'n': n,
        'distances': {v: dist[v] for v in range(n)},
        'parent': {v: (None if parent[v] == -1 else parent[v]) for v in range(n)},
        'tree': tree,
        'in_tree': in_tree,
        'adj': adj,
        'indeg': indeg,
    }


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    indeg = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                indeg[v].add(u)
    dist, parent, tree, in_tree = _bfs(n, adj)
    return _make_state(n, dist, parent, tree, in_tree, adj, indeg)


def _sync(state, u, v, add):
    adj = state['adj']
    indeg = state['indeg']
    if add:
        adj[u].add(v)
        indeg[v].add(u)
    else:
        adj[u].discard(v)
        indeg[v].discard(u)


def insert_edge(graph, edge, state):
    u, v = edge
    _sync(state, u, v, True)
    dist = state['distances']
    parent = state['parent']
    tree = state['tree']
    in_tree = state['in_tree']
    adj = state['adj']

    # Only useful if u is reachable and the edge improves v's distance.
    if dist[u] == -1 or (dist[v] != -1 and dist[u] + 1 >= dist[v]):
        return state

    # v's distance improves to dist[u]+1; re-parent v and cascade.
    old_parent = parent[v]
    if old_parent is not None:
        tree[old_parent].remove(v)
        in_tree[v].remove(old_parent)
    dist[v] = dist[u] + 1
    parent[v] = u
    tree[u].append(v)
    in_tree[v].append(u)

    # Cascade: BFS over the tree from v. For each tree child y of x, if
    # dist[y] > dist[x] + 1, y's distance improves; re-parent y and continue.
    # If dist[y] == dist[x] + 1, y's distance is unchanged (it was already a
    # BFS child of x), so no subtree change is needed below y.
    queue = [v]
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        for y in list(tree[x]):
            if dist[y] > dist[x] + 1:
                p = parent[y]
                tree[p].remove(y)
                in_tree[y].remove(p)
                dist[y] = dist[x] + 1
                parent[y] = x
                tree[x].append(y)
                in_tree[y].append(x)
                queue.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    _sync(state, u, v, False)
    # Simple and always correct: full recompute.
    n = state['n']
    dist, parent, tree, in_tree = _bfs(n, state['adj'])
    state['distances'] = {v: dist[v] for v in range(n)}
    state['parent'] = {v: (None if parent[v] == -1 else parent[v]) for v in range(n)}
    state['tree'] = tree
    state['in_tree'] = in_tree
    return state
