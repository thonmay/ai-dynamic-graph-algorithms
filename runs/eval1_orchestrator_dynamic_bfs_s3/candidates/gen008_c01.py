"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] or None (root/unreachable)
  distances: list, BFS distance from root, -1 if unreachable
  adj:       list of sets of out-neighbors (kept in sync with graph)
  in_adj:    list of sets of in-neighbors
  n:         number of vertices

Insert: if the new edge (u,v) can shorten v's distance (dist[u]+1 < dist[v]),
recompute BFS only over the affected region (distances can only decrease).
Otherwise no change.

Delete: if the deleted edge is not v's tree edge, the BFS tree is still valid
and distances remain correct. If it is the tree edge, run a local
"decrease-only" BFS seeded at v (which may become unreachable, dist -1).
This is sound because:
  - v's new distance is either -1 or exactly 1 + min{dist[u'] : u' in
    in_adj(v) \\ {u}, dist[u'] != -1}, and every such in-neighbor u' has
    dist[u'] < dist[v] (old), so u' is unaffected by the deletion and its
    distance is still correct.
  - every other vertex w != v has an old shortest path P of length
    dist[w] < dist[v] (old). If P does not use v, it is intact. If P does
    use v, then P = r -> ... -> v -> ... -> w, so the prefix to v has
    length dist[v] (old) < dist[w], contradicting that P is a shortest
    path to w. Hence P is intact and dist[w] is unchanged.
So only v's distance can change (increase or to -1), and the local
decrease-only recompute seeded at v propagates the change correctly.
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

    # The root is always reachable at distance 0 with no parent, regardless
    # of its in-neighbors. If the deleted edge's head is the root, just
    # ensure the root's state is correct and return.
    if v == 0:
        dist[0] = 0
        parent[0] = None
        return {
            'parent': parent,
            'distances': dist,
            'adj': adj,
            'in_adj': in_adj,
            'n': n,
        }

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

    # The tree edge of v was deleted. Only v's distance can change
    # (increase or to -1); every other vertex keeps its distance (see
    # module docstring for the argument). Compute v's new distance from
    # its remaining in-neighbors, then run the local decrease-only
    # recompute seeded at v to propagate any change to descendants.
    old_dv = dist[v]  # old distance of v (u was its parent, so old_dv = dist[u]+1)

    best = -1
    best_p = None
    for u2 in in_adj[v]:
        d2 = dist[u2]
        if d2 != -1 and (best == -1 or d2 + 1 < best):
            best = d2 + 1
            best_p = u2
    dist[v] = best
    parent[v] = best_p
    if best != -1:
        parent, dist = _recompute_region(adj, in_adj, n, parent, dist, [v])
    else:
        # v became unreachable. Its old descendants may still be reachable
        # via other in-neighbors (with smaller dist, unaffected by the
        # deletion), so run the decrease-only recompute seeded at all
        # affected vertices (old dist >= old dist[v]) to fix them up.
        seeds = [w for w in range(n)
                 if w != v and (dist[w] == -1 or dist[w] >= old_dv)]
        parent, dist = _recompute_region(adj, in_adj, n, parent, dist, seeds)

    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'in_adj': in_adj,
        'n': n,
    }
