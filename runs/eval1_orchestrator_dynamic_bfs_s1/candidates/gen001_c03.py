"""Dynamic BFS tree from root 0 under single-edge insertions/deletions.

State dict keys:
  parent:    list, parent[v] or None (root and unreachable are None)
  distances: list, BFS distance from root, -1 for unreachable
  adj:       current adjacency matrix (kept in sync; equals the graph arg)
  in_adj:    reverse adjacency matrix
  n:         number of vertices

Insertion: if the new edge (u,v) improves v's distance (dist[u]+1 < dist[v]),
re-root the BFS subtree of v at the new parent and fix distances of the
affected subtree.  Otherwise nothing changes.

Deletion: if the deleted edge is not the tree edge of its head, nothing
changes.  Otherwise the subtree rooted at the head may lose its only
shortest-path parent; we recompute distances for that subtree (and any
vertices whose distance grows) with a bounded BFS, and re-parent affected
vertices to the best in-neighbor at distance d-1.
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
        for v in range(n):
            if adj[u][v] and dist[v] == INF:
                dist[v] = du + 1
                parent[v] = u
                queue.append(v)
    return parent, dist


def init(graph):
    n = len(graph)
    adj = [list(row) for row in graph]
    in_adj = [[0] * n for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(n):
            if row[v]:
                in_adj[v][u] = 1
    parent, dist = _bfs_full(adj, n)
    dist = [d if d != INF else -1 for d in dist]
    return {'parent': parent, 'distances': dist, 'adj': adj,
            'in_adj': in_adj, 'n': n}


def _fix_subtree(state, v, new_parent):
    """v's parent changes to new_parent (or is deleted); recompute
    distances/parents for the subtree of v and any vertices whose distance
    changes as a result."""
    adj = state['adj']
    in_adj = state['in_adj']
    parent = state['parent']
    dist = state['distances']
    n = state['n']

    # Collect the old subtree of v (tree edges).
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)

    sub = []
    stack = [v]
    while stack:
        u = stack.pop()
        sub.append(u)
        for c in children[u]:
            stack.append(c)

    in_sub = [False] * n
    for x in sub:
        in_sub[x] = True

    # For each subtree vertex, find the best in-neighbor outside the subtree.
    best_out = [INF] * n
    for x in sub:
        for y in range(n):
            if in_adj[x][y] and not in_sub[y]:
                d = dist[y]
                if d != -1:
                    cand = d + 1
                    if cand < best_out[x]:
                        best_out[x] = cand

    # BFS within the subtree using all edges among subtree vertices,
    # seeded with best_out.
    import heapq
    heap = []
    new_dist = [INF] * n
    for x in sub:
        if best_out[x] < INF:
            new_dist[x] = best_out[x]
            heapq.heappush(heap, (best_out[x], x))

    while heap:
        d, u = heapq.heappop(heap)
        if d > new_dist[u]:
            continue
        for w in range(n):
            if adj[u][w] and in_sub[w]:
                nd2 = d + 1
                if nd2 < new_dist[w]:
                    new_dist[w] = nd2
                    heapq.heappush(heap, (nd2, w))

    # Update parent and dist for affected vertices.
    for x in sub:
        old_d = dist[x]
        new_d = new_dist[x]
        if new_d == INF:
            dist[x] = -1
            parent[x] = None
        elif new_d != old_d:
            dist[x] = new_d
            # find parent: in-neighbor at distance new_d - 1
            found = None
            for y in range(n):
                if in_adj[x][y] and not in_sub[y] and dist[y] == new_d - 1:
                    found = y
                    break
            if found is None:
                for y in range(n):
                    if in_adj[x][y] and in_sub[y] and dist[y] == new_d - 1:
                        found = y
                        break
            parent[x] = found
        # else: distance unchanged, keep old parent

    state['parent'] = parent
    state['distances'] = dist
    return state


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    in_adj = state['in_adj']
    parent = state['parent']
    dist = state['distances']
    n = state['n']

    adj[u][v] = 1
    in_adj[v][u] = 1

    du = dist[u]
    if du == -1:
        return state

    dv = dist[v]
    if dv != -1 and du + 1 >= dv:
        return state

    # v's distance improves to du+1 (or v was unreachable)
    parent[v] = u
    dist[v] = du + 1
    return _fix_subtree(state, v, u)


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    in_adj = state['in_adj']
    parent = state['parent']
    dist = state['distances']
    n = state['n']

    adj[u][v] = 0
    in_adj[v][u] = 0

    if parent[v] != u:
        return state

    return _fix_subtree(state, v, None)
