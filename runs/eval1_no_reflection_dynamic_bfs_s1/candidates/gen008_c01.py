"""Dynamic BFS tree maintenance for directed graphs, root = 0.

State dict keys:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, distances[v] = BFS distance from root, -1 if unreachable

Insertion: if the new edge (u, v) gives v a strictly shorter distance,
re-run BFS from v, relaxing only edges that improve a distance.

Deletion: if the deleted edge is not v's tree edge, nothing changes.
Otherwise the subtree of v in the BFS tree may have lost its only
shortest-path support.  We recompute distances for exactly the subtree
vertices: a BFS whose initial queue is the subtree vertices that have an
in-edge from a vertex outside the subtree (whose distance is unchanged),
then propagates inside the subtree.  Vertices outside the subtree keep
their old distances, which remain valid because the deleted edge only
removed a path that went through v.
"""

from collections import deque


def _bfs_full(graph):
    """Full BFS from root 0. Returns (parent, distances)."""
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def init(graph):
    parent, dist = _bfs_full(graph)
    return {'parent': parent, 'distances': dist}


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    dist = state['distances']
    n = len(graph)

    # If u is unreachable, the new edge doesn't help anyone.
    if dist[u] == -1:
        return state

    new_d = dist[u] + 1
    if dist[v] == -1 or new_d < dist[v]:
        # v gets a shorter distance; cascade BFS from v.
        dist[v] = new_d
        parent[v] = u
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in range(n):
                if graph[x][y]:
                    if dist[y] == -1 or dx + 1 < dist[y]:
                        dist[y] = dx + 1
                        parent[y] = x
                        q.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    dist = state['distances']
    n = len(graph)

    # If the deleted edge is not v's tree edge, the BFS tree is still valid.
    if parent[v] != u:
        return state

    # v lost its tree edge. Collect the subtree of v in the BFS tree.
    children = [[] for _ in range(n)]
    for x in range(n):
        if parent[x] is not None:
            children[parent[x]].append(x)

    subtree = [False] * n
    q = deque([v])
    subtree[v] = True
    while q:
        x = q.popleft()
        for c in children[x]:
            subtree[c] = True
            q.append(c)

    # Mark subtree vertices as needing recomputation.
    for x in range(n):
        if subtree[x]:
            dist[x] = -1
            parent[x] = None

    # BFS: sources are edges from outside the subtree into it.
    q = deque()
    for x in range(n):
        if not subtree[x]:
            continue
        best_d = -1
        best_p = None
        for a in range(n):
            if subtree[a]:
                continue
            if dist[a] != -1 and graph[a][x]:
                d = dist[a] + 1
                if best_d == -1 or d < best_d:
                    best_d = d
                    best_p = a
        if best_d != -1:
            dist[x] = best_d
            parent[x] = best_p
            q.append(x)

    # BFS within the subtree.
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in range(n):
            if graph[x][y] and subtree[y]:
                if dist[y] == -1 or dx + 1 < dist[y]:
                    dist[y] = dx + 1
                    parent[y] = x
                    q.append(y)

    return state
