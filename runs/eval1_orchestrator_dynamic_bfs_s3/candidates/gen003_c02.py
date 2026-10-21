"""Dynamic BFS tree from a fixed root (vertex 0) under edge insertions/deletions.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, distances[v] = BFS distance or -1
  adj:       list of sets, current out-neighborhoods (kept in sync with graph)
  in_adj:    list of sets, current in-neighborhoods

Insertion: if the new edge (u,v) can shorten v's distance (dist[u]+1 < dist[v]),
recompute BFS from v (with the new edge) and patch the affected subtree.
Deletion: if the deleted edge is the tree edge of v, recompute BFS from v
(restricted to the old subtree) and patch.
Otherwise the BFS tree is unchanged and no work is done.
"""


def _bfs_from(start, adj, dist, parent, start_dist=None, start_parent=None):
    """BFS from `start` using `adj`, but never going to a vertex w with
    dist[w] < dist[start] (those are already settled at smaller distance).
    Returns (dist, parent) for the affected region: dist[w] is the new BFS
    distance for vertices in the affected region, parent[w] the new parent.
    Vertices not reached keep their old values (caller handles).

    If start_dist is None, the caller must have already set dist[start] to
    start's new distance. If start_dist == -1, start is unreachable and is
    not enqueued (its out-neighbors are not reached through it).
    """
    if start_dist is None:
        start_dist = dist[start]
        start_parent = parent[start]
    new_dist = {}
    new_parent = {}
    if start_dist != -1:
        new_dist[start] = start_dist
        new_parent[start] = start_parent
    queue = [start] if start_dist != -1 else []
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        du = new_dist[u]
        for w in adj[u]:
            if w in new_dist:
                continue
            if dist[w] != -1 and dist[w] < start_dist:
                # settled at a strictly smaller distance; cannot be affected
                continue
            if dist[w] != -1 and dist[w] <= du + 1:
                # already at distance <= du+1; a BFS from start cannot improve
                # it (any path through start has length >= d0 + (du+1-d0) = du+1)
                continue
            new_dist[w] = du + 1
            new_parent[w] = u
            queue.append(w)
    # If start is unreachable, any vertex reached through it is also
    # unreachable; mark them all as such so the caller can patch them.
    if start_dist == -1:
        for w in new_dist:
            new_dist[w] = -1
            new_parent[w] = None
    return new_dist, new_parent


def _mark_unreachable(v, adj, dist, parent):
    """Mark v and every vertex whose only paths from the root went through v
    as unreachable. Returns (new_dist, new_parent) for the patch, where
    every entry has dist -1 and parent None.
    """
    new_dist = {v: -1}
    new_parent = {v: None}
    queue = [v]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for w in adj[u]:
            if w in new_dist:
                continue
            if dist[w] == -1:
                continue
            if parent[w] != u:
                # w has a different parent; it may still be reachable via
                # that parent (or another in-neighbor), so do not mark it.
                continue
            new_dist[w] = -1
            new_parent[w] = None
            queue.append(w)
    # After marking, some descendants may still be reachable via in-neighbors
    # outside the marked set (e.g., a cycle back to an ancestor). Run a BFS
    # from each such vertex to propagate reachability to its descendants.
    for w in list(new_dist.keys()):
        if dist[w] == -1:
            # check if w has an in-neighbor with a valid distance
            for a in range(len(dist)):
                if dist[a] != -1 and w in adj[a]:
                    # w is reachable at dist[a]+1
                    new_dist[w] = dist[a] + 1
                    new_parent[w] = a
                    break
    # Now propagate: for each vertex in new_dist with a valid distance,
    # run a BFS to update its descendants.
    for w in list(new_dist.keys()):
        if new_dist[w] != -1:
            nd, np = _bfs_from(w, adj, dist, parent,
                               start_dist=new_dist[w], start_parent=new_parent[w])
            for k, val in nd.items():
                new_dist[k] = val
                new_parent[k] = np[k]
    return new_dist, new_parent


def _apply_patch(state, new_dist, new_parent):
    parent = state['parent']
    distances = state['distances']
    for v, d in new_dist.items():
        parent[v] = new_parent[v]
        distances[v] = d


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    in_adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
                in_adj[v].add(u)
    parent = [None] * n
    distances = [-1] * n
    # BFS from root 0
    if n > 0:
        distances[0] = 0
        queue = [0]
        head = 0
        while head < len(queue):
            u = queue[head]
            head += 1
            for w in adj[u]:
                if distances[w] == -1:
                    distances[w] = distances[u] + 1
                    parent[w] = u
                    queue.append(w)
    return {'parent': parent, 'distances': distances, 'adj': adj, 'in_adj': in_adj}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    in_adj = state['in_adj']
    adj[u].add(v)
    in_adj[v].add(u)
    distances = state['distances']
    parent = state['parent']
    # Only useful if u is reachable and the edge shortens v
    if distances[u] != -1 and distances[v] != -1 and distances[u] + 1 < distances[v]:
        distances[v] = distances[u] + 1
        parent[v] = u
        new_dist, new_parent = _bfs_from(v, adj, distances, parent)
        _apply_patch(state, new_dist, new_parent)
    elif distances[u] != -1 and distances[v] == -1:
        # v becomes reachable
        distances[v] = distances[u] + 1
        parent[v] = u
        new_dist, new_parent = _bfs_from(v, adj, distances, parent)
        _apply_patch(state, new_dist, new_parent)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    in_adj = state['in_adj']
    adj[u].discard(v)
    in_adj[v].discard(u)
    distances = state['distances']
    parent = state['parent']
    # Only a problem if this was v's tree edge
    if parent[v] == u and v != 0:
        # v may be reachable again via another in-neighbor at the same
        # distance; find the best such parent (or None if unreachable).
        best_d = -1
        best_p = None
        for w in in_adj[v]:
            dw = distances[w]
            if dw != -1 and (best_d == -1 or dw < best_d):
                best_d = dw
                best_p = w
        if best_p is None:
            # v and its whole old subtree may be affected; walk the old
            # BFS-tree subtree and mark every descendant unreachable.
            new_dist, new_parent = _mark_unreachable(v, adj, distances, parent)
            _apply_patch(state, new_dist, new_parent)
        else:
            distances[v] = best_d + 1
            parent[v] = best_p
            new_dist, new_parent = _bfs_from(v, adj, distances, parent)
            _apply_patch(state, new_dist, new_parent)
    return state
