"""Dynamic BFS tree from fixed root 0 under directed edge insertions/deletions.

State: dict with
  'parent': list, parent[v] = p (or -1 for root/unreachable)
  'dist':   list, dist[v] = BFS distance from root (or -1 if unreachable)
  'tree':   list of lists, tree[p] = list of children (BFS tree edges)
  'result': dict {'parent': {v: p or None}, 'distances': {v: d}}
"""

from collections import deque


def _result(parent, dist):
    return {'parent': {v: (parent[v] if parent[v] != -1 else None)
                       for v in range(len(dist)) if dist[v] != -1},
            'distances': {v: dist[v] for v in range(len(dist)) if dist[v] != -1}}


def _bfs_full(graph):
    n = len(graph)
    parent = [-1] * n
    dist = [-1] * n
    tree = [[] for _ in range(n)]
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = dist[u] + 1
                parent[v] = u
                tree[u].append(v)
                q.append(v)
    return {'parent': parent, 'dist': dist, 'tree': tree,
            'result': _result(parent, dist)}


def init(graph):
    return _bfs_full(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    dist = state['dist']
    tree = state['tree']
    n = len(graph)

    # If u is unreachable, the edge adds nothing.
    if dist[u] == -1:
        return state
    # If v is already at distance <= dist[u]+1, no improvement possible.
    if dist[v] != -1 and dist[v] <= dist[u] + 1:
        return state

    # v's distance improves to dist[u]+1 (or v becomes reachable).
    new_d = dist[u] + 1
    if dist[v] != -1:
        old_p = parent[v]
        if old_p != -1:
            tree[old_p].remove(v)
    dist[v] = new_d
    parent[v] = u
    tree[u].append(v)

    # Propagate improvements to v's descendants (and beyond).
    q = deque([v])
    while q:
        x = q.popleft()
        for y in range(n):
            if graph[x][y] and dist[y] > dist[x] + 1:
                old_p = parent[y]
                if old_p != -1:
                    tree[old_p].remove(y)
                dist[y] = dist[x] + 1
                parent[y] = x
                tree[x].append(y)
                q.append(y)
    state['result'] = _result(parent, dist)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    dist = state['dist']
    tree = state['tree']
    n = len(graph)

    # Only tree-edge deletions matter.
    if parent[v] != u:
        return state

    # Save old distances before clearing.
    old_dist = {x: dist[x] for x in range(n)}

    # Detach the subtree rooted at v.
    affected = []
    stack = [v]
    while stack:
        x = stack.pop()
        affected.append(x)
        for y in tree[x]:
            stack.append(y)
    aff_set = set(affected)
    for x in affected:
        tree[x] = []
        dist[x] = -1
    tree[u].remove(v)
    parent[v] = -1

    # Max old distance in affected set.
    max_d = max(old_dist[x] for x in affected)

    # Frontier: all vertices not in affected with dist <= max_d.
    frontier = []
    for w in range(n):
        if w not in aff_set and dist[w] != -1 and dist[w] <= max_d:
            frontier.append(w)

    # BFS from frontier into affected set.
    q = deque()
    for w in frontier:
        for y in range(n):
            if graph[w][y] and y in aff_set and dist[y] == -1:
                dist[y] = dist[w] + 1
                parent[y] = w
                tree[w].append(y)
                q.append(y)
    while q:
        x = q.popleft()
        for y in range(n):
            if graph[x][y] and y in aff_set and dist[y] == -1:
                dist[y] = dist[x] + 1
                parent[y] = x
                tree[x].append(y)
                q.append(y)

    state['result'] = _result(parent, dist)
    return state
