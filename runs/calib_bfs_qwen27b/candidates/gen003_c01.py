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
Deletions: incremental - if the deleted edge is not a tree edge, nothing
changes; otherwise the affected subtree is reattached to the nearest
non-subtree in-neighbor (or marked unreachable), with a BFS cascade.
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

    # v's distance improves to dist[u]+1. Re-parent v, then cascade: when x's
    # distance improves, every out-neighbor y of x may now have dist[y] >
    # dist[x] + 1 and must be re-parented to x (or newly discovered).
    old_parent = parent[v]
    if old_parent is not None:
        tree[old_parent].remove(v)
        in_tree[v].remove(old_parent)
    dist[v] = dist[u] + 1
    parent[v] = u
    tree[u].append(v)
    in_tree[v].append(u)

    queue = [v]
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        for y in list(adj[x]):
            if dist[y] > dist[x] + 1:
                p = parent[y]
                if p is not None:
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
    dist = state['distances']
    parent = state['parent']
    tree = state['tree']
    in_tree = state['in_tree']
    indeg = state['indeg']

    # If the deleted edge is not a tree edge, the BFS tree is unchanged.
    if parent[v] != u:
        return state

    # The tree edge (u, v) is gone. Collect the affected subtree.
    subtree = []
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        stack.extend(tree[x])
    in_sub = set(subtree)

    # For each affected vertex, find the best reattachment: the in-neighbor
    # outside the subtree with the smallest distance.
    best = {}
    for x in subtree:
        bd = -1
        bp = None
        for p in indeg[x]:
            if p in in_sub:
                continue
            d = dist[p]
            if d != -1 and (bd == -1 or d + 1 < bd):
                bd = d + 1
                bp = p
        best[x] = (bd, bp)

    # Detach the subtree from its old parents.
    for x in subtree:
        p = parent[x]
        if p is not None:
            tree[p].remove(x)
            in_tree[x].remove(p)
        parent[x] = None

    # Reattach vertices in BFS order (by new distance).
    queue = []
    for x in subtree:
        if best[x][1] is not None:
            dist[x] = best[x][0]
            parent[x] = best[x][1]
            tree[best[x][1]].append(x)
            in_tree[x].append(best[x][1])
            queue.append(x)
        else:
            dist[x] = -1
    queue.sort(key=lambda x: dist[x])

    # Cascade: a reattached vertex may improve any out-neighbor (tree child
    # or not), including vertices that were previously unreachable.
    adj = state['adj']
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        for y in list(adj[x]):
            if dist[y] > dist[x] + 1:
                p = parent[y]
                if p is not None:
                    tree[p].remove(y)
                    in_tree[y].remove(p)
                dist[y] = dist[x] + 1
                parent[y] = x
                tree[x].append(y)
                in_tree[y].append(x)
                queue.append(y)
    return state
