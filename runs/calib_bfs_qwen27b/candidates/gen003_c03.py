"""Dynamic BFS tree from fixed root 0 under directed edge insertions/deletions.

State: dict with
  'parent': list, parent[v] = p or None (unreachable or root)
  'dist':   list, dist[v] = BFS distance or -1 (unreachable)
  'n':      number of vertices

Insertions: incremental BFS from the affected vertex (Frigioni-style).
Deletions:  if the deleted edge is not the tree edge of its head, nothing
changes.  Otherwise the subtree rooted at the head may lose reachability or
find a shorter path; we recompute BFS restricted to the affected region
(the deleted subtree plus any vertex whose tree edge points into it).
"""


def _bfs_from(start, graph, dist, parent, n):
    """BFS starting from `start` (dist[start] already set), updating dist/parent
    in place.  Only relaxes edges; a vertex is finalized when popped."""
    from collections import deque
    q = deque([start])
    while q:
        u = q.popleft()
        du = dist[u]
        row = graph[u]
        for v in range(n):
            if row[v] and (dist[v] < 0 or dist[v] > du + 1):
                dist[v] = du + 1
                parent[v] = u
                q.append(v)


def init(graph):
    n = len(graph)
    dist = [-1] * n
    parent = [None] * n
    dist[0] = 0
    _bfs_from(0, graph, dist, parent, n)
    return {'parent': parent, 'dist': dist, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    dist = state['dist']
    parent = state['parent']
    if dist[u] >= 0 and (dist[v] < 0 or dist[v] > dist[u] + 1):
        # v (and possibly its descendants) can be pulled closer to the root,
        # or v was unreachable and is now reachable for the first time.
        dist[v] = dist[u] + 1
        parent[v] = u
        _bfs_from(v, graph, dist, parent, n)
    return {'parent': parent, 'dist': dist, 'n': n}


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    dist = state['dist']
    parent = state['parent']
    if parent[v] != u:
        # Deleted edge was not v's tree edge: distances and tree unchanged.
        return state
    if dist[v] < 0:
        # v was unreachable; nothing to fix.
        return state

    # v's tree edge is gone.  Collect the subtree of v in the old tree.
    children = [[] for _ in range(n)]
    for w in range(n):
        p = parent[w]
        if p is not None:
            children[p].append(w)

    affected = []
    stack = [v]
    while stack:
        x = stack.pop()
        affected.append(x)
        stack.extend(children[x])
    in_sub = [False] * n
    for x in affected:
        in_sub[x] = True

    # Vertices outside the subtree whose tree edge points into it: their
    # parent is no longer a valid in-neighbor at the right distance.
    outside = []
    for w in range(n):
        if not in_sub[w] and dist[w] >= 0 and parent[w] is not None and in_sub[parent[w]]:
            outside.append(w)

    # Reset the whole affected region.
    for x in affected + outside:
        dist[x] = -1
        parent[x] = None

    # Re-BFS from every boundary vertex: reachable vertices just outside the
    # region that have an edge into it, plus the root if the region contains it.
    from collections import deque
    q = deque()
    seen = [False] * n
    for x in affected + outside:
        for w in range(n):
            if graph[w][x] and dist[w] >= 0 and not seen[w]:
                seen[w] = True
                q.append(w)
    if in_sub[0]:
        dist[0] = 0
        parent[0] = None
        if not seen[0]:
            seen[0] = True
            q.append(0)

    while q:
        u2 = q.popleft()
        du = dist[u2]
        row = graph[u2]
        for v2 in range(n):
            if row[v2] and (dist[v2] < 0 or dist[v2] > du + 1):
                dist[v2] = du + 1
                parent[v2] = u2
                q.append(v2)

    # Safety net: if any vertex in the region was not re-reached, the region
    # logic above missed something; fall back to a full BFS from the root.
    for x in affected + outside:
        if dist[x] < 0:
            dist = [-1] * n
            parent = [None] * n
            dist[0] = 0
            _bfs_from(0, graph, dist, parent, n)
            break

    return {'parent': parent, 'dist': dist, 'n': n}
