"""Dynamic BFS tree maintenance for directed graphs, root = 0.

State dict keys:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, distances[v] = BFS distance from root, -1 if unreachable
  children:  list of lists, children[u] = tree children of u (maintained)
"""

from collections import deque


def _bfs_full(graph):
    """Full BFS from root 0. Returns (parent, distances, children)."""
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    children = [[] for _ in range(n)]
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                children[u].append(v)
                q.append(v)
    return parent, dist, children


def init(graph):
    parent, dist, children = _bfs_full(graph)
    return {'parent': parent, 'distances': dist, 'children': children}


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    dist = state['distances']
    children = state['children']
    n = len(graph)

    # If u is unreachable, the new edge doesn't help anyone.
    if dist[u] == -1:
        return state

    new_d = dist[u] + 1
    if dist[v] == -1 or new_d < dist[v]:
        # v gets a shorter distance; cascade BFS from v.
        # First detach v from its old parent (if any).
        if parent[v] is not None:
            children[parent[v]].remove(v)
        dist[v] = new_d
        parent[v] = u
        children[u].append(v)
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in range(n):
                if graph[x][y]:
                    if dist[y] == -1 or dx + 1 < dist[y]:
                        # y gets a shorter distance; re-parent it.
                        if parent[y] is not None:
                            children[parent[y]].remove(y)
                        dist[y] = dx + 1
                        parent[y] = x
                        children[x].append(y)
                        q.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    dist = state['distances']
    children = state['children']
    n = len(graph)

    # If the deleted edge is not v's tree edge, the BFS tree is still valid.
    if parent[v] != u:
        return state

    # v lost its tree edge. Collect the subtree of v in the BFS tree.
    subtree = set()
    q = deque([v])
    subtree.add(v)
    while q:
        x = q.popleft()
        for c in children[x]:
            subtree.add(c)
            q.append(c)

    # Mark subtree vertices as needing recomputation.
    for x in subtree:
        dist[x] = -1
        parent[x] = None
        children[x] = []

    # BFS: sources are edges from outside the subtree into it.
    q = deque()
    for x in subtree:
        best_d = -1
        best_p = None
        for a in range(n):
            if a in subtree:
                continue
            if dist[a] != -1 and graph[a][x]:
                d = dist[a] + 1
                if best_d == -1 or d < best_d:
                    best_d = d
                    best_p = a
        if best_d != -1:
            dist[x] = best_d
            parent[x] = best_p
            children[best_p].append(x)
            q.append(x)

    # BFS within the subtree.
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in range(n):
            if graph[x][y] and y in subtree:
                if dist[y] == -1 or dx + 1 < dist[y]:
                    dist[y] = dx + 1
                    parent[y] = x
                    children[x].append(y)
                    q.append(y)

    return state
