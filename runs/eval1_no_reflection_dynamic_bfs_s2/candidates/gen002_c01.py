"""Dynamic BFS tree from root 0 under single-edge insertions/deletions.

State dict:
  'parent':    list, parent[v] = BFS parent or None (root/unreachable)
  'distances': list, BFS distance from root, -1 for unreachable
  'adj':       list of sets, current out-neighborhoods (kept in sync)
  'indeg':     list of sets, current in-neighborhoods (kept in sync)

Insertion: if the new edge can shorten v, run a restricted BFS that only
touches vertices whose distance actually improves.

Deletion: if the deleted edge is not the parent edge of its head, nothing
changes.  Otherwise the subtree rooted at the head may be affected; we
recompute distances for exactly that subtree.  The recompute is a BFS that
starts from the boundary (vertices outside the subtree at distance d-1 with
an edge into the subtree) and propagates only inside the subtree.  This is
correct because:
  * every vertex outside the subtree keeps its old (correct) distance, and
  * any new shortest path into the subtree must enter it from a boundary
    vertex at distance d-1 (a vertex at distance d-2 cannot reach a subtree
    vertex in one step, since that would contradict the old distances).
"""

from collections import deque


def _build_adj(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    indeg = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                indeg[v].add(u)
    return adj, indeg


def _bfs_full(adj, n):
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
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
    adj, indeg = _build_adj(graph)
    parent, dist = _bfs_full(adj, n)
    return {'parent': parent, 'distances': dist, 'adj': adj, 'indeg': indeg}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    indeg = state['indeg']
    parent = state['parent']
    dist = state['distances']

    adj[u].add(v)
    indeg[v].add(u)

    # Only useful if u is reachable and the edge can shorten v.
    if dist[u] != -1 and dist[u] + 1 < dist[v]:
        # Restricted BFS: only vertices whose distance improves are enqueued.
        q = deque()
        dist[v] = dist[u] + 1
        parent[v] = u
        q.append(v)
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
    indeg = state['indeg']
    parent = state['parent']
    dist = state['distances']

    adj[u].discard(v)
    indeg[v].discard(u)

    # If v is unreachable, or the deleted edge is not its parent edge,
    # the BFS tree and distances are unchanged.
    if dist[v] == -1 or parent[v] != u:
        return state

    # The subtree rooted at v may be affected. Collect it.
    subtree = set()
    stack = [v]
    while stack:
        x = stack.pop()
        if x in subtree:
            continue
        subtree.add(x)
        for y in adj[x]:
            if parent[y] == x:
                stack.append(y)

    # Boundary: vertices outside the subtree at distance d-1 (d = dist[x])
    # that have an edge into the subtree.  They can serve as new parents.
    boundary = set()
    for x in subtree:
        for w in indeg[x]:
            if w not in subtree and dist[w] == dist[x] - 1:
                boundary.add(w)

    # Mark subtree vertices as invalid; recompute from the boundary.
    for x in subtree:
        dist[x] = -1
        parent[x] = None

    # Seeds: boundary vertices are already at their correct distance;
    # BFS outward from them into the subtree.
    q = deque()
    for w in boundary:
        for x in adj[w]:
            if x in subtree and dist[x] == -1:
                dist[x] = dist[w] + 1
                parent[x] = w
                q.append(x)

    while q:
        x = q.popleft()
        dx = dist[x]
        for y in adj[x]:
            if y in subtree and dist[y] == -1:
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)

    return state
