"""Dynamic BFS tree from fixed root 0 under directed edge insertions/deletions.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, distances[v] = BFS distance from root, -1 if unreachable
  adj:       list of sets, current out-neighborhoods (kept in sync with graph)
  rad:       list, radius[v] = max distance of any vertex in v's BFS subtree
             (subtree = vertices whose tree path passes through v); -1 if v
             unreachable. Used to bound the affected region on deletions.

Insertion: only the target vertex can improve (dist -1 or dist-1); propagate
improvements forward. Deletion: if the deleted edge is not the tree edge of
its head, nothing changes; otherwise the head's subtree may need re-parenting
or may become unreachable. We recompute distances for the affected region
with a bounded BFS (only vertices with dist <= max affected radius), then
rebuild the tree edges inside the region.
"""

from collections import deque


def _bfs_full(adj, n):
    dist = [-1] * n
    dist[0] = 0
    q = [0]
    i = 0
    while i < len(q):
        u = q[i]
        i += 1
        du = dist[u] + 1
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = du
                q.append(v)
    return dist


def _rebuild_tree(adj, dist):
    parent = [None] * len(dist)
    for v in range(len(dist)):
        if v == 0 or dist[v] == -1:
            continue
        for u in adj[v]:
            if dist[u] == dist[v] - 1:
                parent[v] = u
                break
    return parent


def _compute_rad(parent, dist):
    n = len(dist)
    rad = [-1] * n
    children = {v: [] for v in range(n)}
    for v in range(n):
        if parent[v] is not None:
            children[parent[v]].append(v)
    order = sorted(children.keys(), key=lambda x: -dist[x])
    for v in order:
        m = dist[v]
        for c in children[v]:
            if rad[c] > m:
                m = rad[c]
        rad[v] = m
    return rad


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        for v in range(n):
            if graph[u][v]:
                adj[u].add(v)
    dist = _bfs_full(adj, n)
    parent = _rebuild_tree(adj, dist)
    rad = _compute_rad(parent, dist)
    return {'parent': parent, 'distances': dist, 'adj': adj, 'rad': rad}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].add(v)
    dist = state['distances']
    parent = state['parent']
    rad = state['rad']
    n = len(dist)
    # v can improve if dist[u] + 1 < dist[v]
    if dist[u] != -1 and dist[u] + 1 < dist[v]:
        # v improves; propagate forward
        dq = deque([v])
        dist[v] = dist[u] + 1
        parent[v] = u
        while dq:
            x = dq.popleft()
            dx = dist[x] + 1
            for y in adj[x]:
                if dx < dist[y]:
                    dist[y] = dx
                    parent[y] = x
                    dq.append(y)
        # recompute rad from scratch (correctness first)
        rad = _compute_rad(parent, dist)
    return {'parent': parent, 'distances': dist, 'adj': adj, 'rad': rad}


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].discard(v)
    dist = state['distances']
    parent = state['parent']
    rad = state['rad']
    n = len(dist)
    # If the deleted edge is not the tree edge of v, nothing changes.
    if parent[v] != u:
        return {'parent': parent, 'distances': dist, 'adj': adj, 'rad': rad}
    # v's subtree may be affected.
    # Build subtree of v from parent pointers.
    children = {v: [] for v in range(n)}
    for x in range(n):
        if parent[x] is not None:
            children[parent[x]].append(x)
    subtree = set()
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.add(x)
        for c in children[x]:
            stack.append(c)
    # Recompute distances for subtree vertices.
    # Sources: in-neighbors of subtree vertices that are NOT in subtree
    # (their dist is fixed).
    nd = list(dist)
    # Reset subtree vertices to -1 temporarily for recomputation
    for x in subtree:
        nd[x] = -1
    # Multi-source BFS: start from in-neighbors of subtree that are outside.
    dq = deque()
    for x in subtree:
        for p in range(n):
            if x in adj[p]:  # p -> x edge
                if p not in subtree and nd[p] != -1:
                    d = nd[p] + 1
                    if d < nd[x]:
                        nd[x] = d
                        dq.append(x)
    # BFS within subtree
    while dq:
        x = dq.popleft()
        dx = nd[x] + 1
        for y in adj[x]:
            if y in subtree and dx < nd[y]:
                nd[y] = dx
                dq.append(y)
    # Rebuild parent for subtree vertices
    np = list(parent)
    for x in subtree:
        if nd[x] == -1:
            np[x] = None
            continue
        np[x] = None
        for p in range(n):
            if x in adj[p] and nd[p] == nd[x] - 1:
                np[x] = p
                break
    # Recompute rad for all vertices
    nr = _compute_rad(np, nd)
    return {'parent': np, 'distances': nd, 'adj': adj, 'rad': nr}
