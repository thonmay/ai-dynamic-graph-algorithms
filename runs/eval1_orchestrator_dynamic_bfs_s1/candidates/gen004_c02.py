"""Dynamic BFS tree from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, distances[v] = BFS distance from root, -1 if unreachable
  adj:       list of sets of out-neighbors (kept in sync with the matrix)
  n:         number of vertices

Insertions use the standard incremental BFS repair (only affected vertices
change, each vertex's distance can only decrease). Deletions use a local
repair: if the deleted edge is not the parent edge of its head, nothing
changes; otherwise the subtree rooted at the head is re-rooted by a
multi-source BFS from the boundary (vertices at the same level that have an
edge into the subtree), which is exactly the correct BFS repair. If the
subtree cannot be re-rooted, the affected part is cut off (distances -1).
"""

from collections import deque


def _bfs_full(adj, n, root=0):
    dist = [-1] * n
    parent = [None] * n
    dist[root] = 0
    q = deque([root])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    parent, dist = _bfs_full(adj, n)
    return {'parent': parent, 'distances': dist, 'adj': adj, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    n = state['n']
    adj[u].add(v)
    parent = state['parent']
    dist = state['distances']
    if dist[u] != -1 and (dist[v] == -1 or dist[u] + 1 < dist[v]):
        # v improves; propagate the improvement.
        dist[v] = dist[u] + 1
        parent[v] = u
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in adj[x]:
                if dist[y] == -1 or dx + 1 < dist[y]:
                    dist[y] = dx + 1
                    parent[y] = x
                    q.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    n = state['n']
    adj[u].discard(v)
    parent = state['parent']
    dist = state['distances']
    if parent[v] != u:
        # Deleted edge is not the parent edge of v: the BFS tree is intact.
        return state
    # v loses its parent. Collect the subtree rooted at v in the tree.
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)
    subtree = []
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        stack.extend(children[x])
    in_sub = [False] * n
    for x in subtree:
        in_sub[x] = True
    # Cut the whole subtree: distances become -1, parents None.
    for x in subtree:
        dist[x] = -1
        parent[x] = None
    # Multi-source BFS from the boundary: every vertex outside the subtree
    # that has an edge into the subtree is a valid source (its distance is
    # unchanged and correct, since only the subtree was cut).  This also
    # covers the case where the old parent u is itself inside the subtree
    # (e.g. a 2-cycle u<->v), in which case u is not a valid source.
    # Seed each subtree vertex at the MINIMUM boundary distance (not the
    # first boundary vertex by id), then propagate.
    q = deque()
    for w in range(n):
        if in_sub[w]:
            continue
        if dist[w] == -1:
            continue
        for x in adj[w]:
            if in_sub[x]:
                cand = dist[w] + 1
                if dist[x] == -1 or cand < dist[x]:
                    dist[x] = cand
                    parent[x] = w
    for x in subtree:
        if dist[x] != -1:
            q.append(x)
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if dist[y] == -1 or dx + 1 < dist[y]:
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)
    # The re-rooted part may now reach other cut-off vertices of the subtree
    # (e.g. via cross edges), so run the standard insertion-style propagation
    # over the whole graph to pick them up.
    for x in subtree:
        if dist[x] != -1:
            for y in adj[x]:
                if dist[y] == -1 or dist[x] + 1 < dist[y]:
                    dist[y] = dist[x] + 1
                    parent[y] = x
                    q.append(y)
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if dist[y] == -1 or dx + 1 < dist[y]:
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)
    return state
