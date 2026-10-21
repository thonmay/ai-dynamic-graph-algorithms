"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] or None (root/unreachable)
  distances: list, BFS distance from root, -1 if unreachable
  adj:       list of sets of out-neighbors (kept in sync with graph)
  in_adj:    list of sets of in-neighbors
  n:         number of vertices

Insert: if the new edge (u,v) can shorten v's distance (dist[u]+1 < dist[v]),
recompute BFS only over the affected region (distance decreases only).
Otherwise no change.

Delete: if the deleted edge is not the tree edge of v (parent[v]==u), the BFS
tree is still valid and distances remain correct. If it is the tree edge,
recompute only the affected region: vertices whose distance may INCREASE or
that may become unreachable. The region is found by a BFS from v over the
current tree edges (away from the root); every vertex in the region is
re-discovered by a BFS restricted to the region, using the old distances of
unaffected vertices as boundary conditions.
"""

from collections import deque


def _bfs_full(adj, n):
    """Full BFS from root 0. Returns (parent, distances)."""
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _recompute_region_decrease(adj, in_adj, n, parent, dist, seeds):
    """Recompute distances/parents for vertices whose distance may have DECREASED.

    seeds: iterable of vertices that are known to have a valid (possibly new,
    smaller) distance and whose out-edges should be relaxed. We run a BFS
    restricted to vertices whose current dist is >= the minimum seed dist,
    because only those can change. Vertices with smaller dist are unaffected.

    This is only sound for distance decreases (edge insertions).
    """
    if not seeds:
        return parent, dist

    min_sd = min(dist[s] for s in seeds)

    new_dist = {}
    new_parent = {}

    # Initialize queue with seeds
    q = deque()
    for s in seeds:
        new_dist[s] = dist[s]
        new_parent[s] = parent[s]
        q.append(s)

    # Also add affected vertices that have an unaffected in-neighbor
    # (an in-neighbor u with dist[u] < min_sd, i.e., u is unaffected)
    for v in range(n):
        if v in new_dist:
            continue
        if dist[v] != -1 and dist[v] < min_sd:
            continue  # unaffected
        # v is affected (dist >= min_sd or -1); check in-neighbors
        for u in in_adj[v]:
            if dist[u] != -1 and dist[u] < min_sd:
                # u is unaffected, so v can be reached at dist[u]+1
                new_dist[v] = dist[u] + 1
                new_parent[v] = u
                q.append(v)
                break

    # BFS relaxation
    while q:
        u = q.popleft()
        du = new_dist[u]
        for v in adj[u]:
            # v can only be improved if it is affected (dist[v] >= min_sd or -1)
            if dist[v] != -1 and dist[v] < min_sd:
                continue  # unaffected, cannot change
            cand = du + 1
            if v not in new_dist or cand < new_dist[v]:
                new_dist[v] = cand
                new_parent[v] = u
                q.append(v)

    # Apply: for vertices in new_dist, update; for affected vertices NOT in
    # new_dist, they become unreachable.
    for v in range(n):
        if dist[v] != -1 and dist[v] < min_sd:
            continue  # unaffected
        if v in new_dist:
            dist[v] = new_dist[v]
            parent[v] = new_parent[v]
        else:
            dist[v] = -1
            parent[v] = None

    return parent, dist


def _recompute_region_increase(adj, in_adj, n, parent, dist, v):
    """Recompute distances/parents for vertices whose distance may have
    INCREASED or that may become unreachable, after the tree edge of v was
    deleted.

    Region: all vertices reachable from v by following the current (old) tree
    edges away from the root. Every vertex in the region had its distance
    determined (in the old tree) through v, so its distance can only increase
    or become -1. Vertices outside the region keep their old distance and
    parent, and their old distances are valid lower bounds that the new BFS
    must respect.

    The new distances inside the region are found by a BFS restricted to the
    region, seeded with region vertices that have an in-neighbor outside the
    region (whose old distance is unchanged).
    """
    # 1. Find the affected region by walking the old tree away from the root.
    in_region = [False] * n
    region = []
    q = deque([v])
    in_region[v] = True
    while q:
        u = q.popleft()
        region.append(u)
        for w in range(n):
            if parent[w] == u and not in_region[w]:
                in_region[w] = True
                q.append(w)

    # 2. BFS restricted to the region.
    new_dist = {}
    new_parent = {}
    q = deque()

    # Seeds: region vertices with an in-neighbor outside the region.
    for w in region:
        for u in in_adj[w]:
            if not in_region[u] and dist[u] != -1:
                new_dist[w] = dist[u] + 1
                new_parent[w] = u
                q.append(w)
                break

    while q:
        u = q.popleft()
        du = new_dist[u]
        for w in adj[u]:
            if not in_region[w]:
                continue  # unaffected vertex, keep old distance
            cand = du + 1
            if w not in new_dist or cand < new_dist[w]:
                new_dist[w] = cand
                new_parent[w] = u
                q.append(w)

    # 3. Apply: region vertices in new_dist get new values; the rest become
    # unreachable. Non-region vertices are untouched.
    for w in region:
        if w in new_dist:
            dist[w] = new_dist[w]
            parent[w] = new_parent[w]
        else:
            dist[w] = -1
            parent[w] = None

    return parent, dist


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    in_adj = [set() for _ in range(n)]
    for u in range(n):
        for v in range(n):
            if graph[u][v]:
                adj[u].add(v)
                in_adj[v].add(u)
    parent, dist = _bfs_full(adj, n)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'in_adj': in_adj,
        'n': n,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    in_adj = state['in_adj']
    parent = state['parent']
    dist = state['distances']

    adj[u].add(v)
    in_adj[v].add(u)

    # If u is reachable and dist[u]+1 < dist[v], v's distance can improve.
    if dist[u] != -1 and (dist[v] == -1 or dist[u] + 1 < dist[v]):
        # v's distance improves to dist[u]+1; this may cascade to v's
        # descendants. Recompute region seeded at v.
        dist[v] = dist[u] + 1
        parent[v] = u
        parent, dist = _recompute_region_decrease(adj, in_adj, n, parent, dist, [v])

    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'in_adj': in_adj,
        'n': n,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    in_adj = state['in_adj']
    parent = state['parent']
    dist = state['distances']

    adj[u].discard(v)
    in_adj[v].discard(u)

    # If the deleted edge is not v's tree edge, the BFS tree remains valid
    # and all distances stay correct (deleting a non-tree edge cannot
    # increase any BFS distance).
    if parent[v] != u:
        return {
            'parent': parent,
            'distances': dist,
            'adj': adj,
            'in_adj': in_adj,
            'n': n,
        }

    # The tree edge of v was deleted. v may need a new parent or become
    # unreachable; its descendants may be affected. Recompute only the
    # affected region (distances can only increase here).
    parent, dist = _recompute_region_increase(adj, in_adj, n, parent, dist, v)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'in_adj': in_adj,
        'n': n,
    }
