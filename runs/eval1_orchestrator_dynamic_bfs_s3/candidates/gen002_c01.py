"""Dynamic BFS tree from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  'parent':    list, parent[v] = p (BFS parent) or None (root/unreachable)
  'distances': list, distances[v] = BFS distance from root, -1 if unreachable
  'adj':       list of sets, current out-neighborhood of each vertex
  'rad':       list, rad[v] = number of in-neighbors u with dist[u] == dist[v]-1
               (only meaningful for reachable v)

Correctness invariant after every update:
  - parent[root] is None; parent[v] is None iff v is unreachable.
  - for reachable v != root: parent[v] is a true in-neighbor and
    distances[parent[v]] == distances[v] - 1.
  - distances are the true BFS distances.

Update strategy:
  - Insertion: if the new edge can shorten some vertices, run a local BFS
    restricted to vertices whose distance actually decreases. The improved
    set is closed (a vertex not improved cannot be improved via an improved
    vertex), so this is exact. Otherwise O(1).
  - Deletion: if the deleted edge is not the BFS parent edge of its head,
    O(1) (distances can only increase on deletion, and the head still has a
    shortest path via its parent). Otherwise the affected subtree may lose
    its BFS property; we recompute distances/parents for exactly the affected
    vertices (those in the subtree of the deleted edge's head) with a local
    BFS that reuses the old distances as upper bounds. Vertices outside the
    subtree keep valid distances: their old parent chains do not go through
    the deleted edge, so their distances are still achievable, and they
    cannot be improved (deletion only increases distances).
"""


def _bfs_full(adj, n, root):
    """Full BFS from root. Returns (parent, distances)."""
    parent = [None] * n
    dist = [-1] * n
    dist[root] = 0
    queue = [root]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        du = dist[u]
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                queue.append(v)
    return parent, dist


def _build_rad(adj, dist, n):
    """rad[v] = number of in-neighbors u with dist[u] == dist[v] - 1."""
    rad = [0] * n
    for u in range(n):
        du = dist[u]
        if du < 0:
            continue
        for v in adj[u]:
            if dist[v] == du + 1:
                rad[v] += 1
    return rad


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    root = 0
    parent, dist = _bfs_full(adj, n, root)
    rad = _build_rad(adj, dist, n)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'rad': rad,
        'graph': [list(row) for row in graph],
    }


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    n = len(adj)
    adj[u].add(v)
    dist = state['distances']
    parent = state['parent']
    rad = state['rad']
    if dist[v] >= 0:
        rad[v] += 1

    du = dist[u]
    if du < 0:
        # u unreachable: edge cannot help anyone.
        return state

    if dist[v] == -1:
        # v becomes reachable at du+1; propagate to newly reachable vertices.
        improved = {v}
        newdist = {v: du + 1}
        newparent = {v: u}
        queue = [v]
        head = 0
        while head < len(queue):
            x = queue[head]
            head += 1
            dx = newdist[x]
            for y in adj[x]:
                if dist[y] == -1 and y not in improved:
                    improved.add(y)
                    newdist[y] = dx + 1
                    newparent[y] = x
                    queue.append(y)
        for x in improved:
            dist[x] = newdist[x]
            parent[x] = newparent[x]
        # recompute rad for improved vertices
        for x in improved:
            dx = newdist[x]
            c = 0
            for a in range(n):
                if dist[a] == dx - 1 and x in adj[a]:
                    c += 1
            rad[x] = c
        return state

    if dist[v] <= du + 1:
        # v's distance does not decrease; no vertex can be improved
        # (any improvement would have to go through v first).
        return state

    # v's distance decreases to du+1; propagate improvements.
    # improved set: vertices whose distance strictly decreases.
    # Closedness: if x is improved and x->y with old dist[y] > new dist[x]+1,
    # then y is improved too. If y is not improved, old dist[y] <=
    # new dist[x]+1, so no path through x improves y.
    improved = set()
    newdist = {v: du + 1}
    newparent = {v: u}
    improved.add(v)
    queue = [v]
    head = 0
    while head < len(queue):
        x = queue[head]
        head += 1
        dx = newdist[x]
        for y in adj[x]:
            if dist[y] > dx + 1 and y not in improved:
                improved.add(y)
                newdist[y] = dx + 1
                newparent[y] = x
                queue.append(y)

    for x in improved:
        dist[x] = newdist[x]
        parent[x] = newparent[x]

    # Update rad for improved vertices: count in-neighbors at new dist-1.
    # In-neighbors at new dist-1 are either improved (with new dist) or
    # non-improved (old dist == new dist-1). Scan all vertices.
    for x in improved:
        dx = newdist[x]
        c = 0
        for a in range(n):
            if dist[a] == dx - 1 and x in adj[a]:
                c += 1
        rad[x] = c
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    n = len(adj)
    adj[u].discard(v)
    dist = state['distances']
    parent = state['parent']
    rad = state['rad']
    if dist[v] >= 0:
        rad[v] -= 1

    if parent[v] != u:
        # Deleted edge is not v's BFS parent. v keeps its parent and its
        # distance is still achievable; distances can only increase on
        # deletion, so nothing changes.
        return state

    # The deleted edge was v's BFS parent. Collect v's subtree in the BFS tree.
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)

    subtree = set()
    stack = [v]
    while stack:
        x = stack.pop()
        if x in subtree:
            continue
        subtree.add(x)
        for c in children[x]:
            stack.append(c)

    # Check whether any subtree vertex lost all in-neighbors at dist-1.
    need_fix = False
    for x in subtree:
        if rad[x] == 0:
            need_fix = True
            break
    if not need_fix:
        return state

    # Local repair on the subtree: recompute distances for subtree vertices
    # using old distances as upper bounds. Boundary in-edges (from outside
    # the subtree) provide the seeds.
    #
    # Correct approach: the new distances of subtree vertices are the BFS
    # distances in the graph where outside-subtree vertices are fixed at
    # their old distances. This is a shortest-path problem with unit edges
    # and some vertices having fixed source distances. Run multi-source BFS:
    # seed each subtree vertex x with candidate = min over in-neighbors a
    # (outside subtree) of dist[a]+1, and also allow propagation within the
    # subtree.
    import heapq

    INF = 1 << 60
    nd = {x: INF for x in subtree}
    np_ = {x: None for x in subtree}
    heap = []
    for x in subtree:
        best = INF
        bp = None
        for a in range(n):
            if a in subtree:
                continue
            da = dist[a]
            if da < 0:
                continue
            if x in adj[a]:
                cand = da + 1
                if cand < best:
                    best = cand
                    bp = a
        if best < INF:
            nd[x] = best
            np_[x] = bp
            heapq.heappush(heap, (best, x))

    while heap:
        d, x = heapq.heappop(heap)
        if d > nd[x]:
            continue
        for y in adj[x]:
            if y not in subtree:
                continue
            cand = d + 1
            if cand < nd[y]:
                nd[y] = cand
                np_[y] = x
                heapq.heappush(heap, (cand, y))

    # Apply: vertices with nd == INF become unreachable.
    for x in subtree:
        if nd[x] == INF:
            dist[x] = -1
            parent[x] = None
        else:
            dist[x] = nd[x]
            parent[x] = np_[x]

    # Update rad for subtree vertices.
    for x in subtree:
        dx = dist[x]
        if dx < 0:
            rad[x] = 0
            continue
        c = 0
        for a in range(n):
            if dist[a] == dx - 1 and x in adj[a]:
                c += 1
        rad[x] = c
    return state
