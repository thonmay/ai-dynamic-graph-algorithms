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

Delete: if the deleted edge is not v's tree edge (parent[v]==u), the BFS tree
remains valid and distances stay correct. If it is the tree edge, run a
localized "increase" repair: find v's true new distance from its unaffected
in-neighbors; if v is unreachable, detach the whole subtree rooted at v;
otherwise re-parent v and re-run the decrease repair over the subtree to fix
descendants.
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


def _recompute_region(adj, in_adj, n, parent, dist, seeds, affected):
    """Recompute distances/parents for vertices in `affected` (a set of
    vertices whose distance may have changed, e.g. a BFS-tree subtree).

    seeds: iterable of vertices in `affected` that are known to have a valid
    (possibly new) distance and whose out-edges should be relaxed.

    Soundness: every in-neighbor u of an affected vertex v with
    dist[u] < min(dist[s] for s in seeds) is itself unaffected (its distance
    cannot change), so it provides a valid boundary distance. The affected
    set must be closed under tree children (a subtree), so no unaffected
    vertex can be reached through an affected one.

    Works for both distance decreases (insertions) and increases (deletions
    of a tree edge, after the seed has been given its true new distance).
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
    for v in affected:
        if v in new_dist:
            continue
        # v is affected; check in-neighbors
        for u in in_adj[v]:
            if u in affected:
                continue
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
            # v can only be improved if it is affected
            if v not in affected:
                continue  # unaffected, cannot change
            cand = du + 1
            if v not in new_dist or cand < new_dist[v]:
                new_dist[v] = cand
                new_parent[v] = u
                q.append(v)

    # Apply: for vertices in new_dist, update; for affected vertices NOT in
    # new_dist, they become unreachable.
    for v in affected:
        if v in new_dist:
            dist[v] = new_dist[v]
            parent[v] = new_parent[v]
        else:
            dist[v] = -1
            parent[v] = None

    return parent, dist


def _subtree(adj, n, parent, root):
    """Return the set of vertices in the BFS-tree subtree rooted at `root`
    (including root)."""
    children = {root: []}
    for v in range(n):
        p = parent[v]
        if p is not None and p in children:
            children[p].append(v)
    order = set()
    q = deque([root])
    while q:
        u = q.popleft()
        order.add(u)
        for w in children[u]:
            children[w] = []
            q.append(w)
    return order


def _find_new_parent(adj, in_adj, n, dist, v, old_dist):
    """After v's tree edge was deleted, find v's true new distance and a
    valid parent, using only in-neighbors outside the subtree (which are
    unaffected). Returns (new_dist, new_parent) or (None, None) if v is
    unreachable.

    Soundness: every in-neighbor u of v with dist[u] < old_dist is unaffected
    by the deletion (its own distance cannot increase: any shortest path to u
    that used v would have length >= old_dist + 1 > dist[u]). The true new
    distance of v is min(dist[u]+1) over all in-neighbors u, and any such u
    with dist[u] < old_dist attains it.
    """
    best = None
    best_u = None
    for u in in_adj[v]:
        du = dist[u]
        if du == -1:
            continue
        if du + 1 < old_dist:
            # unaffected in-neighbor
            if best is None or du + 1 < best:
                best = du + 1
                best_u = u
    if best is None:
        return None, None
    return best, best_u


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
        # descendants. Recompute region seeded at v over v's subtree.
        #
        # The affected set is v's subtree PLUS every vertex whose current
        # distance is >= dist[u]+1 (the new distance of v). This is needed
        # because a vertex w with dist[w] >= dist[u]+1 that is NOT in v's
        # subtree can also be improved through the new edge (e.g. w was
        # unreachable, or w's old parent chain went through v's old distance
        # level). Vertices with dist < dist[u]+1 are unaffected.
        new_dv = dist[u] + 1
        affected = set()
        for w in range(n):
            if dist[w] == -1 or dist[w] >= new_dv:
                affected.add(w)
        # v's subtree is a subset of the above (v has dist >= new_dv or -1,
        # and every descendant has dist >= dist[v] >= new_dv or -1), so no
        # need to add it explicitly.
        dist[v] = new_dv
        parent[v] = u
        parent, dist = _recompute_region(adj, in_adj, n, parent, dist, [v], affected)

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

    # The tree edge of v was deleted. Only the subtree rooted at v can be
    # affected. Find v's true new distance from its unaffected in-neighbors.
    old_dist = dist[v]
    new_d, new_p = _find_new_parent(adj, in_adj, n, dist, v, old_dist)

    # Affected set: v's subtree PLUS every vertex whose current distance is
    # >= new_d (or unreachable). This is needed because a vertex w with
    # dist[w] >= new_d that is NOT in v's subtree can also be re-parented
    # through the new (larger) distance of v. Vertices with dist < new_d
    # are unaffected.
    #
    # IMPORTANT: compute the affected set BEFORE updating dist[v], because
    # v's old distance (old_dist >= new_d) is what makes v affected.
    affected = set()
    for w in range(n):
        if dist[w] == -1 or dist[w] >= new_d:
            affected.add(w)

    if new_d is None:
        # v is unreachable; detach the whole subtree.
        for w in affected:
            dist[w] = -1
            parent[w] = None
    else:
        # v stays reachable at a larger distance; re-parent it and fix the
        # affected region (distances inside can only increase, then the
        # repair propagates the correct values).
        dist[v] = new_d
        parent[v] = new_p
        parent, dist = _recompute_region(adj, in_adj, n, parent, dist, [v], affected)

    return {
        'parent': parent,
        'distances': dist,
        'adj': adj,
        'in_adj': in_adj,
        'n': n,
    }
