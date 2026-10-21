"""Dynamic BFS tree from fixed root 0 under directed edge insert/delete.

State dict:
  parent:    list, parent[v] or None (root/unreachable)
  distances: list, BFS distance from root, -1 if unreachable
  adj:       current adjacency matrix
  in_adj:    reverse adjacency matrix

Strategy:
  - insert_edge: if the new edge (u,v) can shorten v's distance (dist[u]+1 <
    dist[v]), re-root the BFS subtree of v at the new parent u via a local
    BFS.  Otherwise nothing changes.
  - delete_edge: if the deleted edge is not the tree edge of any vertex,
    nothing changes.  Otherwise the subtree of the orphaned vertex may have
    lost its only shortest path; we recompute BFS restricted to the affected
    region (the orphaned subtree plus any vertices whose distance could
    change), which is far smaller than a full recompute in typical cases.
"""

from collections import deque


def _bfs_full(adj, n, root=0):
    parent = [None] * n
    dist = [-1] * n
    dist[root] = 0
    q = deque([root])
    while q:
        u = q.popleft()
        du = dist[u]
        for v in range(n):
            if adj[u][v] and dist[v] == -1:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return parent, dist


def _rebuild_in_adj(adj, n):
    in_adj = [[0] * n for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(n):
            if row[v]:
                in_adj[v][u] = 1
    return in_adj


def init(graph):
    n = len(graph)
    parent, dist = _bfs_full(graph, n)
    return {
        'parent': parent,
        'distances': dist,
        'adj': [row[:] for row in graph],
        'in_adj': _rebuild_in_adj(graph, n),
    }


def _subtree_of(v, parent, n):
    """Return the set of vertices in the BFS subtree rooted at v (v included)."""
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)
    seen = set()
    stack = [v]
    while stack:
        u = stack.pop()
        if u in seen:
            continue
        seen.add(u)
        stack.extend(children[u])
    return seen


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    in_adj = state['in_adj']

    # sync the stored matrices with the current graph (only the flipped entry)
    adj[u][v] = graph[u][v]
    in_adj[v][u] = graph[u][v]

    if dist[u] == -1:
        # u unreachable: edge cannot help anyone
        return state

    new_d = dist[u] + 1
    if dist[v] != -1 and new_d >= dist[v]:
        # no improvement
        return state

    # v's distance improves to new_d; re-root v's subtree under u.
    if dist[v] != -1:
        affected = _subtree_of(v, parent, n)
    else:
        affected = set()

    # Set v's new parent and distance.
    parent[v] = u
    dist[v] = new_d

    # Local BFS to fix up the subtree.
    q = deque([v])
    while q:
        x = q.popleft()
        dx = dist[x]
        for y in range(n):
            if not adj[x][y]:
                continue
            cand = dx + 1
            if y == u:
                continue
            if dist[y] == -1:
                # was unreachable, now reachable
                dist[y] = cand
                parent[y] = x
                q.append(y)
            elif y in affected and cand < dist[y]:
                dist[y] = cand
                parent[y] = x
                q.append(y)
            # else: keep existing (it is <= cand, so still valid)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    dist = state['distances']
    adj = state['adj']
    in_adj = state['in_adj']

    adj[u][v] = graph[u][v]
    in_adj[v][u] = graph[u][v]

    # If the deleted edge is not a tree edge, the BFS tree is still valid.
    if parent[v] != u:
        return state

    # v lost its tree parent.  The subtree of v may need re-parenting or
    # may become unreachable.  Recompute BFS restricted to the affected
    # region: the subtree of v plus any vertex that could be reached at a
    # smaller distance through it (none, since distances only increase or
    # stay).  So we only need to fix the subtree of v.
    affected = _subtree_of(v, parent, n)
    # v itself is in affected.

    # For each vertex in the affected set (in BFS order from v), try to find
    # a new parent: an in-neighbor w with dist[w] == dist[x] - 1 (w not in
    # affected, or already fixed).  If none, the vertex (and possibly its
    # descendants) becomes unreachable.
    #
    # We process in increasing distance order.  Vertices in `affected` keep
    # their old distance if they can find a valid parent; otherwise they
    # become unreachable and so do their descendants (unless a descendant
    # has its own valid parent outside the subtree).

    # Order affected vertices by (old) distance.
    affected_list = sorted(affected, key=lambda x: dist[x])

    # We'll track which vertices are still reachable.
    # Start: v has no parent (its tree edge was deleted).
    # For each x in affected_list: find an in-neighbor w with dist[w] ==
    # dist[x] - 1 that is reachable (w not in affected, or w in affected
    # and still reachable).  If found, parent[x] = w.  Else x becomes
    # unreachable: dist[x] = -1, parent[x] = None.

    reachable = set()
    # Vertices outside affected are all still reachable as before.
    # We only need to check reachability for vertices in affected.

    for x in affected_list:
        target = dist[x] - 1
        found = None
        for w in range(n):
            if not in_adj[x][w]:
                continue
            if dist[w] != target:
                continue
            if w in affected:
                if w not in reachable:
                    continue
            # w is reachable (outside affected or fixed inside)
            found = w
            break
        if found is not None:
            parent[x] = found
            reachable.add(x)
        else:
            parent[x] = None
            dist[x] = -1
    return state
