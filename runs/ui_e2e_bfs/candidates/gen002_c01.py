"""Dynamic BFS tree from fixed root 0 under single-edge insert/delete.

State dict:
  parent:    list, parent[v] = BFS parent or None (root/unreachable)
  distances: list, BFS distance from root, -1 for unreachable
  in_edges:  list of sets, in_edges[v] = {u : graph[u][v] == 1}
  out_edges: list of sets, out_edges[v] = {w : graph[v][w] == 1}

Insert: if the new edge (u,v) can shorten v (dist[u]+1 < dist[v]), do a
Frigioni-style local update: v and its affected subtree move to distance
dist[u]+1; BFS from the moved set fixes the rest.
Delete: if the deleted edge was v's parent, v's subtree may be orphaned;
recompute distances for the orphaned subtree by BFS from its boundary
in-neighbors (which are unaffected by the deletion).
"""

from collections import deque


def _bfs(graph, root):
    n = len(graph)
    dist = [-1] * n
    parent = [None] * n
    dist[root] = 0
    q = deque([root])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _build_state(graph):
    n = len(graph)
    parent, dist = _bfs(graph, 0)
    in_edges = [set() for _ in range(n)]
    out_edges = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                out_edges[u].add(v)
                in_edges[v].add(u)
    return {
        'parent': parent,
        'distances': dist,
        'in_edges': in_edges,
        'out_edges': out_edges,
    }


def init(graph):
    return _build_state(graph)


def _insert_fix(graph, u, v, state):
    """Handle insertion of edge (u,v)."""
    n = len(graph)
    parent = state['parent']
    dist = state['distances']
    in_edges = state['in_edges']
    out_edges = state['out_edges']

    out_edges[u].add(v)
    in_edges[v].add(u)

    # Case 1: v was unreachable; the new edge may make it (and its
    # subtree) reachable.
    if dist[v] == -1:
        if dist[u] == -1:
            return state
        dist[v] = dist[u] + 1
        parent[v] = u
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            for y in out_edges[x]:
                if dist[y] == -1:
                    dist[y] = dx + 1
                    parent[y] = x
                    q.append(y)
        return state

    # Case 2: v reachable; check if the new edge shortens it.
    if dist[u] == -1:
        return state
    new_d = dist[u] + 1
    if new_d >= dist[v]:
        return state

    # Collect the affected subtree: v and descendants whose distance
    # must increase or be re-derived.
    affected = []
    stack = [v]
    while stack:
        x = stack.pop()
        affected.append(x)
        for y in out_edges[x]:
            if parent[y] == x:
                stack.append(y)

    # Mark affected vertices as needing recompute.
    for x in affected:
        dist[x] = -1
        parent[x] = None

    # v gets its new distance from u.
    dist[v] = new_d
    parent[v] = u

    # BFS from v (and any affected vertex that still has a valid
    # in-neighbor outside the affected set) to restore distances.
    affected_set = set(affected)
    q = deque()
    q.append(v)
    for x in affected:
        if x == v:
            continue
        # find best in-neighbor with known distance
        best = -1
        best_p = None
        for p in in_edges[x]:
            if p not in affected_set and dist[p] != -1 and (best == -1 or dist[p] < best):
                best = dist[p]
                best_p = p
        if best != -1:
            dist[x] = best + 1
            parent[x] = best_p
            q.append(x)

    while q:
        x = q.popleft()
        dx = dist[x]
        for y in out_edges[x]:
            if dist[y] == -1:
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)

    return state


def _delete_fix(graph, u, v, state):
    """Handle deletion of edge (u,v)."""
    n = len(graph)
    parent = state['parent']
    dist = state['distances']
    in_edges = state['in_edges']
    out_edges = state['out_edges']

    out_edges[u].discard(v)
    in_edges[v].discard(u)

    if parent[v] != u:
        # v's parent is not the deleted edge; but v's distance might
        # still be affected if u was the only in-neighbor at dist-1.
        # Actually if parent[v] != u, v's tree edge is intact, so v and
        # its subtree keep valid distances. No fix needed.
        return state

    # v's parent was u; v's subtree may be orphaned.
    affected = []
    stack = [v]
    while stack:
        x = stack.pop()
        affected.append(x)
        for y in out_edges[x]:
            if parent[y] == x:
                stack.append(y)

    for x in affected:
        dist[x] = -1
        parent[x] = None

    # BFS from boundary: affected vertices that have an in-neighbor
    # outside the affected set.
    affected_set = set(affected)
    q = deque()
    for x in affected:
        best = -1
        best_p = None
        for p in in_edges[x]:
            if p not in affected_set and dist[p] != -1:
                if best == -1 or dist[p] < best:
                    best = dist[p]
                    best_p = p
        if best != -1:
            dist[x] = best + 1
            parent[x] = best_p
            q.append(x)

    # BFS from the seeded boundary vertices.  Each affected vertex is
    # enqueued at most once (at its first assignment), and BFS order
    # guarantees the first assignment is the minimum possible distance,
    # so no re-shortening is needed.
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in out_edges[x]:
            if dist[y] == -1:
                dist[y] = dx + 1
                parent[y] = x
                q.append(y)
            elif dist[y] > dx + 1:
                # Defensive: should not fire given BFS ordering, but
                # keep the state consistent if it ever does.
                dist[y] = dx + 1
                parent[y] = x
                for z in out_edges[y]:
                    if parent[z] == y:
                        dist[z] = -1
                        parent[z] = None
                q.append(y)

    return state


def insert_edge(graph, edge, state):
    u, v = edge
    return _insert_fix(graph, u, v, state)


def delete_edge(graph, edge, state):
    u, v = edge
    return _delete_fix(graph, u, v, state)
