"""Dynamic BFS tree from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  parent:    list, parent[v] = BFS parent (None for root/unreachable)
  distances: list, distances[v] = BFS distance from root (-1 if unreachable)
  adj:       current adjacency matrix (kept in sync with the graph argument)

Strategy:
  - insert: if the new edge (u,v) can shorten v (dist[u]+1 < dist[v]),
    re-parent v and cascade the improvement to v's subtree (Frigioni-style
    incremental update). Otherwise nothing changes.
  - delete: if the deleted edge is not the tree edge of its head, nothing
    changes. Otherwise the subtree rooted at the head may be broken:
    recompute distances for that subtree only, using a BFS restricted to the
    subtree plus the already-correct outside vertices as sources.
"""

INF = float('inf')


def _bfs_full(adj, n):
    dist = [INF] * n
    parent = [None] * n
    dist[0] = 0
    queue = [0]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        du = dist[u]
        row = adj[u]
        for v in range(n):
            if row[v] and dist[v] == INF:
                dist[v] = du + 1
                parent[v] = u
                queue.append(v)
    dist = [d if d != INF else -1 for d in dist]
    return parent, dist


def init(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph, n)
    return {'parent': parent, 'distances': dist, 'adj': [row[:] for row in graph], 'n': n}


def _reparent(v, new_parent, parent, dist):
    """Re-parent v and cascade the distance improvement to its subtree."""
    dist[v] = dist[new_parent] + 1
    parent[v] = new_parent
    queue = [v]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        du = dist[u]
        for w in range(len(parent)):
            if parent[w] == u and dist[w] > du + 1:
                dist[w] = du + 1
                parent[w] = u
                queue.append(w)


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'] = [row[:] for row in graph]
    parent = state['parent']
    dist = state['distances']
    n = state['n']
    if dist[u] >= 0 and dist[v] >= 0 and dist[u] + 1 < dist[v]:
        _reparent(v, u, parent, dist)
    elif dist[u] >= 0 and dist[v] < 0:
        # v becomes reachable
        dist[v] = dist[u] + 1
        parent[v] = u
        queue = [v]
        head = 0
        while head < len(queue):
            x = queue[head]
            head += 1
            dx = dist[x]
            for y in range(n):
                if state['adj'][x][y] and dist[y] < 0:
                    dist[y] = dx + 1
                    parent[y] = x
                    queue.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'] = [row[:] for row in graph]
    parent = state['parent']
    dist = state['distances']
    n = state['n']
    if parent[v] != u:
        return state
    # The tree edge of v was deleted: subtree rooted at v may be broken.
    # (If v was unreachable, its subtree is unreachable too; nothing to do.)
    if dist[v] < 0:
        return state
    adj = state['adj']
    # Collect the subtree.
    children = [[] for _ in range(n)]
    for w in range(n):
        if parent[w] is not None:
            children[parent[w]].append(w)
    subtree = []
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        stack.extend(children[x])
    sub_set = set(subtree)
    # If the deleted edge was the only in-edge of v, the whole subtree
    # becomes unreachable immediately.
    only_in = True
    for w in range(n):
        if adj[w][v]:
            only_in = False
            break
    if only_in:
        for x in subtree:
            dist[x] = -1
            parent[x] = None
        return state
    # Recompute distances for subtree vertices: BFS from the outside
    # (already-correct vertices) plus internal edges.
    INF2 = float('inf')
    ndist = {x: INF2 for x in subtree}
    nparent = {x: None for x in subtree}
    queue = []
    # Sources: outside vertices with edges into the subtree.
    for x in subtree:
        for w in range(n):
            if adj[w][x] and dist[w] >= 0:
                d = dist[w] + 1
                if d < ndist[x]:
                    ndist[x] = d
                    nparent[x] = w
                    queue.append(x)
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        dx = ndist[x]
        for y in range(n):
            if adj[x][y] and y in sub_set and dx + 1 < ndist[y]:
                ndist[y] = dx + 1
                nparent[y] = x
                queue.append(y)
    # (Vertices with no in-edge from outside and no in-edge from a reached
    # subtree vertex stay INF and are marked unreachable below.)
    for x in subtree:
        if ndist[x] == INF2:
            dist[x] = -1
            parent[x] = None
        else:
            dist[x] = ndist[x]
            parent[x] = nparent[x]
    return state
