"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] or None (root/unreachable)
  distances: list, BFS distance from root, -1 if unreachable
  adj:       list of sets of out-neighbors (kept in sync with graph)
  in_adj:    list of sets of in-neighbors
  n:         number of vertices

Insert: if the new edge (u,v) can shorten v's distance (dist[u]+1 < dist[v]),
recompute BFS only over the affected region. Otherwise no change.

Delete: if the deleted edge is not the tree edge of v (parent[v]==u), the BFS
tree is still valid and distances remain correct. If it is the tree edge,
recompute BFS over the affected region (v and its tree descendants).
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


def _recompute_region(adj, in_adj, n, parent, dist, seeds):
    """Recompute distances/parents for vertices whose distance may have changed.

    seeds: iterable of vertices that are known to have a valid (possibly new)
    distance and whose out-edges should be relaxed. We run a BFS restricted to
    vertices whose current dist is >= the minimum seed dist, because only those
    can change. Vertices with smaller dist are unaffected.
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
        parent, dist = _recompute_region(adj, in_adj, n, parent, dist, [v])

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
    # unreachable; its descendants may be affected.
    # Find v's new best distance: min over in-neighbors u' of dist[u']+1.
    best = -1
    best_p = None
    for u2 in in_adj[v]:
        if dist[u2] != -1:
            d = dist[u2] + 1
            if best == -1 or d < best:
                best = d
                best_p = u2

    if best == -1:
        # v becomes unreachable; so do all its tree descendants.
        # Collect descendants of v in the tree.
        children = [[] for _ in range(n)]
        for x in range(n):
            if parent[x] is not None:
                children[parent[x]].append(x)
        affected = []
        q = deque([v])
        while q:
            x = q.popleft()
            affected.append(x)
            for c in children[x]:
                q.append(c)
        affected_set = set(affected)
        # Set them unreachable temporarily
        for x in affected:
            dist[x] = -1
            parent[x] = None
        # Now check if any affected vertex has an in-neighbor outside
        # the affected set (or with valid dist).
        seeds = []
        for x in affected:
            for u2 in in_adj[x]:
                if u2 not in affected_set and dist[u2] != -1:
                    dist[x] = dist[u2] + 1
                    parent[x] = u2
                    seeds.append(x)
                    break
        if seeds:
            parent, dist = _recompute_region(adj, in_adj, n, parent, dist, seeds)
        # Any affected vertex still with dist -1 stays unreachable.
        # But _recompute_region may have touched non-affected unreachable
        # vertices. For safety, do a full BFS.
        parent, dist = _bfs_full(adj, n)
        return {
            'parent': parent,
            'distances': dist,
            'adj': adj,
            'in_adj': in_adj,
            'n': n,
        }
    else:
        # v gets a new parent at distance best.
        dist[v] = best
        parent[v] = best_p
        # Recompute region seeded at v to fix descendants.
        parent, dist = _recompute_region(adj, in_adj, n, parent, dist, [v])
        return {
            'parent': parent,
            'distances': dist,
            'adj': adj,
            'in_adj': in_adj,
            'n': n,
        }
