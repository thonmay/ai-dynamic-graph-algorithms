"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] or None (root/unreachable)
  distances: list, BFS distance from root, -1 if unreachable
  adj:       current adjacency matrix (kept in sync by the update calls)

Insertions: local fix. If the new edge (u,v) can shorten v (or, if v is
unreachable, make v reachable), re-root the BFS from v with the new
distances as upper bounds; only vertices whose distance actually improves
are touched.

Deletions: if the deleted edge is not the tree edge of its child, nothing
changes. Otherwise the subtree below the child may be orphaned: BFS from the
child's parent (and from any other reachable vertex that has an edge into the
subtree) to find the best reattachment; vertices that cannot be reached are
marked unreachable.
"""

INF = float('inf')


def _bfs_bounded(adj, start, dist, parent, n):
    """BFS from start using current dist as upper bounds.

    Returns (changed, new_dist, new_parent) where changed is the set of
    vertices whose distance improved (or became reachable).
    """
    new_dist = list(dist)
    new_parent = list(parent)
    changed = set()
    if new_dist[start] == -1:
        new_dist[start] = 0
        new_parent[start] = None
        changed.add(start)
    queue = [start]
    i = 0
    while i < len(queue):
        u = queue[i]
        i += 1
        du = new_dist[u]
        row = adj[u]
        for v in range(n):
            if row[v] and du + 1 < new_dist[v]:
                new_dist[v] = du + 1
                new_parent[v] = u
                changed.add(v)
                queue.append(v)
    return changed, new_dist, new_parent


def _bfs_from_frontier(adj, frontier, dist, parent, n):
    """BFS from a set of frontier vertices, using current dist as upper
    bounds. Each frontier vertex keeps its current distance (already set by
    the caller); the BFS propagates improvements to their descendants.

    Returns (changed, new_dist, new_parent).
    """
    new_dist = list(dist)
    new_parent = list(parent)
    changed = set()
    queue = list(frontier)
    i = 0
    while i < len(queue):
        u = queue[i]
        i += 1
        du = new_dist[u]
        row = adj[u]
        for v in range(n):
            if row[v] and du + 1 < new_dist[v]:
                new_dist[v] = du + 1
                new_parent[v] = u
                changed.add(v)
                queue.append(v)
    return changed, new_dist, new_parent


def _bfs_unbounded(adj, start, n):
    """Plain BFS from start; returns (dist, parent) with -1/None for
    unreachable vertices."""
    dist = [-1] * n
    parent = [None] * n
    dist[start] = 0
    queue = [start]
    i = 0
    while i < len(queue):
        u = queue[i]
        i += 1
        du = dist[u]
        row = adj[u]
        for v in range(n):
            if row[v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                queue.append(v)
    return dist, parent


def _rebuild(adj, n):
    dist, parent = _bfs_unbounded(adj, 0, n)
    return {'parent': parent, 'distances': dist, 'adj': adj}


def init(graph):
    n = len(graph)
    adj = [list(row) for row in graph]
    return _rebuild(adj, n)


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(state['adj'])
    adj = state['adj']
    adj[u][v] = 1
    dist = state['distances']
    parent = state['parent']

    # Only useful if u is reachable and the edge improves v's distance
    # (treating -1 as infinity, so a newly reachable v counts).
    dv = dist[v] if dist[v] != -1 else INF
    if dist[u] != -1 and dist[u] + 1 < dv:
        # Pre-seed v with its new distance and parent so the bounded BFS
        # propagates improvements to v's descendants without treating v
        # as the root.
        dist = list(dist)
        parent = list(parent)
        dist[v] = dist[u] + 1
        parent[v] = u
        # Frontier: v plus every reachable vertex w that has an edge into v
        # and whose distance is strictly less than v's new distance. Such a
        # w could give v (or v's descendants) an even shorter path.
        frontier = [v]
        for w in range(n):
            if w != v and dist[w] != -1 and adj[w][v] and dist[w] < dist[v]:
                frontier.append(w)
        changed, new_dist, new_parent = _bfs_from_frontier(adj, frontier, dist, parent, n)
        if changed:
            dist = new_dist
            parent = new_parent
        # The frontier BFS only propagates improvements to vertices whose
        # distance strictly decreases. A vertex that was unreachable before
        # and is reachable only through v (not through any frontier vertex)
        # is never relaxed. Run a plain BFS from v to reach such vertices;
        # it cannot worsen any distance already set.
        if dist[v] != -1:
            d2, p2 = _bfs_unbounded(adj, v, n)
            for x in range(n):
                if d2[x] != -1 and (dist[x] == -1 or d2[x] < dist[x]):
                    dist[x] = d2[x]
                    parent[x] = p2[x]
            # The plain BFS from v treats v as its own root (distance 0);
            # restore v's true distance and parent relative to the real
            # root.
            dist[v] = dist[u] + 1
            parent[v] = u
            # The plain BFS from v may have assigned a parent to a vertex
            # that was already reachable with a strictly smaller distance
            # (the BFS from v treats v as its own root, so its distances
            # are off by dist[v]). Re-run the frontier BFS to fix such
            # vertices.
            frontier2 = [v]
            for w in range(n):
                if w != v and dist[w] != -1 and adj[w][v] and dist[w] < dist[v]:
                    frontier2.append(w)
            changed2, new_dist2, new_parent2 = _bfs_from_frontier(adj, frontier2, dist, parent, n)
            if changed2:
                dist = new_dist2
                parent = new_parent2
            # The plain BFS from v may have assigned a parent to a vertex
            # that was already reachable with a strictly smaller distance
            # (the BFS from v treats v as its own root, so its distances
            # are off by dist[v]). Re-run the frontier BFS to fix such
            # vertices.
            frontier3 = [v]
            for w in range(n):
                if w != v and dist[w] != -1 and adj[w][v] and dist[w] < dist[v]:
                    frontier3.append(w)
            changed3, new_dist3, new_parent3 = _bfs_from_frontier(adj, frontier3, dist, parent, n)
            if changed3:
                dist = new_dist3
                parent = new_parent3
    state['parent'] = parent
    state['distances'] = dist
    state['adj'] = adj
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(state['adj'])
    adj = state['adj']
    adj[u][v] = 0
    dist = state['distances']
    parent = state['parent']

    # If the deleted edge is not v's tree edge, the BFS tree is untouched.
    if parent[v] != u:
        state['adj'] = adj
        return state

    # v's subtree may be orphaned. Find all vertices whose parent chain
    # passes through v (i.e. descendants of v in the tree, including v).
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
        stack.extend(children[x])

    # BFS from u (v's old parent) with the old distances as upper bounds,
    # but restricted so that vertices outside the subtree keep their old
    # distances (they are unaffected). Vertices inside the subtree get new
    # distances if reachable; otherwise they become unreachable.
    new_dist = list(dist)
    new_parent = list(parent)
    # Mark subtree vertices as needing reassignment.
    for x in subtree:
        new_dist[x] = INF
        new_parent[x] = None

    # BFS from u, only relaxing into subtree vertices (others keep old dist).
    queue = [u]
    i = 0
    while i < len(queue):
        x = queue[i]
        i += 1
        dx = new_dist[x]
        row = adj[x]
        for y in range(n):
            if row[y] and y in subtree and dx + 1 < new_dist[y]:
                new_dist[y] = dx + 1
                new_parent[y] = x
                queue.append(y)

    # Any subtree vertex still at INF is unreachable.
    for x in subtree:
        if new_dist[x] == INF:
            new_dist[x] = -1
            new_parent[x] = None

    state['parent'] = new_parent
    state['distances'] = new_dist
    state['adj'] = adj
    return state
