"""Dynamic BFS tree from fixed root 0 under single-edge insertions/deletions.

State dict:
  'parent':    list, parent[v] = BFS parent (None for root / unreachable)
  'distances': list, BFS distance from root, -1 if unreachable
  'adj':       list of sets, current out-neighborhood
  'rad':       list, rad[v] = # in-neighbors u with dist[u] == dist[v]-1
               (0 for unreachable v)

Insertion (u,v):
  - if dist[u]+1 < dist[v] (or v was unreachable): v's distance drops to
    dist[u]+1; re-parent v and its whole BFS subtree via a BFS restricted
    to that subtree.
  - otherwise only rad[v] may increase.

Deletion (u,v):
  - if parent[v] != u: only rad[v] may decrease.
  - otherwise v's subtree may be broken. Region = subtree(v) plus every
    vertex whose rad drops to 0. Recompute dist/parent for the region by a
    BFS seeded from region vertices that still have a valid in-neighbor
    outside the region (or are the root). Unreached region vertices become
    unreachable. Only the region is touched.
"""

from collections import deque


def _subtree(adj, parent, v):
    """Vertices in the BFS tree subtree rooted at v (including v)."""
    out = []
    q = deque([v])
    while q:
        x = q.popleft()
        out.append(x)
        for y in adj[x]:
            if parent[y] == x:
                q.append(y)
    return out


def _rebuild_rad(adj, dist, rad, affected):
    """Recompute rad[w] for w in affected from scratch."""
    for w in affected:
        rw = 0
        dw = dist[w]
        if dw >= 0:
            for x in range(len(adj)):
                if w in adj[x] and dist[x] == dw - 1:
                    rw += 1
        rad[w] = rw


def _full_bfs(adj, dist, parent):
    """Full BFS from root 0; overwrites dist and parent in place."""
    n = len(adj)
    for i in range(n):
        dist[i] = -1
        parent[i] = None
    if n == 0:
        return
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        du = dist[u]
        for w in adj[u]:
            if dist[w] == -1:
                dist[w] = du + 1
                parent[w] = u
                q.append(w)


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    dist = [-1] * n
    parent = [None] * n
    _full_bfs(adj, dist, parent)
    rad = [0] * n
    for u in range(n):
        du = dist[u]
        if du >= 0:
            for w in adj[u]:
                if dist[w] == du + 1:
                    rad[w] += 1
    return {'parent': parent, 'distances': dist, 'adj': adj, 'rad': rad, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    dist = state['distances']
    parent = state['parent']
    rad = state['rad']
    adj[u].add(v)

    du, dv = dist[u], dist[v]
    if du >= 0 and (dv == -1 or du + 1 < dv):
        # v's distance drops (or v was unreachable); re-parent v and its
        # BFS subtree.
        sub = _subtree(adj, parent, v)
        subset = set(sub)
        dist[v] = du + 1
        parent[v] = u
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in adj[x]:
                if y in subset and dist[y] > dx + 1:
                    dist[y] = dx + 1
                    parent[y] = x
                    q.append(y)
        affected = set(sub)
        for x in sub:
            for y in adj[x]:
                affected.add(y)
        _rebuild_rad(adj, dist, rad, affected)
    else:
        if du >= 0 and dv == du + 1:
            rad[v] += 1
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    dist = state['distances']
    parent = state['parent']
    rad = state['rad']
    adj[u].discard(v)

    if parent[v] != u:
        # non-tree edge: only rad[v] may decrease
        if dist[u] >= 0 and dist[v] == dist[u] + 1:
            rad[v] -= 1
        return state

    # tree edge deleted: v's subtree may be broken
    sub = _subtree(adj, parent, v)
    region = set(sub)
    if dist[u] >= 0 and dist[v] == dist[u] + 1:
        rad[v] -= 1
    for x in sub:
        if x != v and rad[x] == 0:
            region.add(x)

    # BFS over the region, seeded by region vertices that have a valid
    # in-neighbor outside the region (or are the root).
    dist2 = dist[:]
    parent2 = parent[:]
    q = deque()
    for w in region:
        if w == 0:
            dist2[w] = 0
            parent2[w] = None
            q.append(w)
            continue
        seeded = False
        for x in range(len(adj)):
            if w in adj[x] and x not in region and dist[x] >= 0 \
                    and dist[x] + 1 == dist[w]:
                if parent[w] != x:
                    parent2[w] = x
                seeded = True
                break
        if seeded:
            q.append(w)
    while q:
        x = q.popleft()
        dx = dist2[x]
        for y in adj[x]:
            if y in region and dist2[y] == -1:
                dist2[y] = dx + 1
                parent2[y] = x
                q.append(y)
    for w in region:
        if dist2[w] == -1:
            parent2[w] = None

    dist[:] = dist2
    parent[:] = parent2

    affected = set(region)
    for x in region:
        for y in adj[x]:
            affected.add(y)
    _rebuild_rad(adj, dist, rad, affected)
    return state
