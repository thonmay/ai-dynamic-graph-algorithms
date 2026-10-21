"""Dynamic BFS tree maintenance for directed graphs, root = 0.

State dict keys:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, distances[v] = BFS distance from root, -1 if unreachable
  children:  list of lists, children[u] = tree children of u
  in_tree:   list of bool, whether edge (parent[v], v) is a tree edge
"""

from collections import deque


def _bfs_full(graph):
    """Full BFS from root 0. Returns (parent, distances, children, in_tree)."""
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    children = [[] for _ in range(n)]
    in_tree = [False] * n
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
                in_tree[v] = True
                q.append(v)
    return parent, dist, children, in_tree


def init(graph):
    parent, dist, children, in_tree = _bfs_full(graph)
    return {'parent': parent, 'distances': dist,
            'children': children, 'in_tree': in_tree}


def _set_parent(state, v, p):
    """Reparent v to p (or None), updating children lists and in_tree."""
    parent = state['parent']
    children = state['children']
    in_tree = state['in_tree']
    old = parent[v]
    if old is not None:
        children[old].remove(v)
        in_tree[v] = False
    parent[v] = p
    if p is not None:
        children[p].append(v)
        in_tree[v] = True


def insert_edge(graph, edge, state):
    u, v = edge
    dist = state['distances']
    n = len(graph)

    # If u is unreachable, the new edge doesn't help anyone.
    if dist[u] == -1:
        return state

    new_d = dist[u] + 1
    if dist[v] == -1 or new_d < dist[v]:
        # v gets a shorter distance; cascade BFS from v
        _set_parent(state, v, u)
        dist[v] = new_d
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in range(n):
                if graph[x][y]:
                    if dist[y] == -1 or dx + 1 < dist[y]:
                        _set_parent(state, y, x)
                        dist[y] = dx + 1
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
    children = state['children']
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
    # Clear children lists of subtree vertices (their children are in subtree).
    for x in subtree:
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

    # BFS within the subtree
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in range(n):
            if graph[x][y] and y in subtree:
                if dist[y] == -1 or dx + 1 < dist[y]:
                    if parent[y] is not None:
                        children[parent[y]].remove(y)
                    dist[y] = dx + 1
                    parent[y] = x
                    children[x].append(y)
                    q.append(y)

    return state
