"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, BFS distance from root, -1 for unreachable
  out:       list of sets, current out-neighbors (kept in sync with graph)
  in:        list of sets, current in-neighbors
"""

INF = float('inf')


def _bfs_full(graph):
    n = len(graph)
    dist = [-1] * n
    parent = [None] * n
    dist[0] = 0
    queue = [0]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return parent, dist


def init(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph)
    out = [set() for _ in range(n)]
    inn = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                out[u].add(v)
                inn[v].add(u)
    return {'parent': parent, 'distances': dist, 'out': out, 'in': inn}


def insert_edge(graph, edge, state):
    u, v = edge
    out = state['out']
    inn = state['in']
    if v in out[u]:
        return state
    out[u].add(v)
    inn[v].add(u)
    dist = state['distances']
    parent = state['parent']
    if dist[u] == -1:
        # u unreachable: no reachable vertex's distance can improve
        return state
    if dist[v] != -1 and dist[v] <= dist[u] + 1:
        # v already at least as close; nothing improves
        return state
    # v's distance improves to dist[u]+1; propagate improvements
    dist[v] = dist[u] + 1
    parent[v] = u
    queue = [v]
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        for y in out[x]:
            if dist[y] > dist[x] + 1:
                dist[y] = dist[x] + 1
                parent[y] = x
                queue.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    out = state['out']
    inn = state['in']
    if v not in out[u]:
        return state
    out[u].discard(v)
    inn[v].discard(u)
    parent = state['parent']
    dist = state['distances']
    if parent[v] != u:
        # deleted edge was not in the BFS tree; distances unchanged
        return state
    # v (and possibly its subtree) may lose its shortest path.
    # Collect the affected subtree.
    n = len(dist)
    children = [[] for _ in range(n)]
    for x in range(n):
        if parent[x] is not None:
            children[parent[x]].append(x)
    affected = []
    stack = [v]
    while stack:
        x = stack.pop()
        affected.append(x)
        stack.extend(children[x])
    affected_set = set(affected)
    # reset
    for x in affected:
        dist[x] = -1
        parent[x] = None
    # seed queue with affected vertices that have a non-affected in-neighbor
    queue = []
    for x in affected:
        best = INF
        bp = None
        for p in inn[x]:
            if p not in affected_set and dist[p] != -1 and dist[p] + 1 < best:
                best = dist[p] + 1
                bp = p
        if bp is not None:
            dist[x] = best
            parent[x] = bp
            queue.append(x)
    # BFS within affected set using only edges from already-fixed vertices
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        for y in out[x]:
            if y in affected_set and dist[y] > dist[x] + 1:
                dist[y] = dist[x] + 1
                parent[y] = x
                queue.append(y)
    # second pass: affected vertices may now be reachable via other affected
    # vertices that were seeded later; re-scan boundary in-neighbors
    changed = True
    while changed:
        changed = False
        for x in affected:
            if dist[x] == -1:
                for p in inn[x]:
                    if p not in affected_set and dist[p] != -1:
                        dist[x] = dist[p] + 1
                        parent[x] = p
                        changed = True
                        break
    return state
