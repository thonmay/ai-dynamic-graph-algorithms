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
run a local "increase" repair: v (and possibly descendants) may need a new
parent at the same level, a longer path, or become unreachable. Only the
subtree rooted at v is touched; the rest of the tree is provably unaffected.
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

    # Apply: for vertices in new_dist, update. For affected vertices NOT in
    # new_dist, verify reachability explicitly: if x has an in-neighbor y
    # with a valid (already-correct) distance dist[y] != -1 and
    # dist[y] + 1 == dist[x], then x is still reachable at its old distance
    # (an insertion cannot increase any distance), so keep x reachable and
    # re-parent it to y. Otherwise x is genuinely unreachable.
    for v in range(n):
        if dist[v] != -1 and dist[v] < min_sd:
            continue  # unaffected
        if v in new_dist:
            dist[v] = new_dist[v]
            parent[v] = new_parent[v]
        elif dist[v] != -1:
            # x was reachable at dist[v] >= min_sd but the restricted BFS
            # did not discover it. Check whether it still has a valid
            # in-neighbor at distance dist[v] - 1.
            kept = False
            for y in in_adj[v]:
                if dist[y] != -1 and dist[y] + 1 == dist[v]:
                    parent[v] = y
                    kept = True
                    break
            if not kept:
                dist[v] = -1
                parent[v] = None
        # else: dist[v] was already -1, stays -1

    return parent, dist


def _repair_after_tree_edge_delete(adj, in_adj, n, parent, dist, v):
    """Repair the BFS tree after the tree edge (parent[v], v) was deleted.

    Only vertices in the subtree rooted at v (in the old tree) can change.
    A subtree vertex's new shortest path may enter the subtree at any vertex
    (via an in-neighbor outside the subtree) and then travel along edges
    INSIDE the subtree (including non-tree cross/back edges). So we:
      1. compute entry[x] = min{ dist[u]+1 : u in in_adj[x], u outside subtree }
      2. run a BFS over the subgraph induced by the subtree, seeded with the
         finite entry distances, relaxing along in-subtree edges.
    Vertices with no finite distance become unreachable.
    """
    # Collect the subtree rooted at v in BFS order.
    subtree = []
    q = deque([v])
    while q:
        x = q.popleft()
        subtree.append(x)
        for w in adj[x]:
            if parent[w] == x:
                q.append(w)

    sub_set = set(subtree)

    # Entry distances from outside the subtree.
    INF = float('inf')
    new_dist = {}
    new_parent = {}
    q = deque()
    for x in subtree:
        best = INF
        bp = None
        for u in in_adj[x]:
            if u in sub_set:
                continue
            du = dist[u]
            if du == -1:
                continue
            cand = du + 1
            if cand < best:
                best = cand
                bp = u
        if best != INF:
            new_dist[x] = best
            new_parent[x] = bp
            q.append(x)

    # BFS inside the subtree (all edges unit weight).
    # The queue is NOT monotone: a vertex can be re-discovered at a smaller
    # distance after it was already popped (e.g. entry 5, then reached at 3
    # via an in-subtree edge). So we must re-relax on every pop, and we must
    # not skip a vertex just because it already has a (larger) distance.
    # This is a Bellman-Ford-style relaxation over the induced subgraph.
    # (In practice, with unit weights and the entry-seeding structure, the
    # queue is nearly monotone, but the re-relaxation guard makes it robust.)
    while q:
        y = q.popleft()
        dy = new_dist[y]
        for w in adj[y]:
            if w not in sub_set:
                continue
            cand = dy + 1
            if w not in new_dist or cand < new_dist[w]:
                new_dist[w] = cand
                new_parent[w] = y
                q.append(w)

    # Apply.
    for x in subtree:
        if x in new_dist:
            dist[x] = new_dist[x]
            parent[x] = new_parent[x]
        else:
            dist[x] = -1
            parent[x] = None

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

    # The tree edge of v was deleted. Repair locally: only the subtree
    # rooted at v can change.
    parent, dist = _repair_after_tree_edge_delete(adj, in_adj, n, parent, dist, v)
    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'in_adj': in_adj,
        'n': n,
    }
