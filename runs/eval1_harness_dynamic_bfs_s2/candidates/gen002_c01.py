"""Dynamic BFS tree from a fixed root (vertex 0) under edge flips.

State is a dict with two list fields, indexed by vertex:
  parent[v]    - the BFS-tree parent of v (None for the root and for
                 unreachable vertices)
  distances[v] - the true BFS distance from the root (-1 if unreachable)

Fast path: an update that cannot change the BFS tree returns immediately.
  * insert (u, v): if u is unreachable, or dist[v] <= dist[u] + 1, the new
    edge gives no shorter path, so nothing changes.
  * delete (u, v): if (u, v) is not v's tree edge (parent[v] != u), no vertex
    loses its tree path, so nothing changes.

Slow path: only the affected region is recomputed, never the whole graph.
  * insert that improves v: region = vertices reachable from v (their distance
    can only drop through the new edge).
  * delete of v's tree edge: region = the subtree of v (the only vertices
    whose tree path used the deleted edge).

The region is recomputed with a boundary-seeded Dijkstra: vertices outside the
region keep their (unchanged) distances, and the new distance of a region
vertex is the shortest path from the boundary into it. Because every out-
neighbor of a reachable vertex is itself reachable, and a vertex's distance is
set by its in-neighbors, this is exact for both regions.
"""

import heapq


def init(graph):
    n = len(graph)
    parent, dist = _full_bfs(graph, n, 0)
    return {"parent": parent, "distances": dist}


def insert_edge(graph, edge, state):
    u, v = edge
    dist = state["distances"]
    parent = state["parent"]
    n = len(dist)
    if dist[u] == -1:
        return state  # u unreachable: no path root -> ... -> u -> v
    if dist[v] != -1 and dist[v] <= dist[u] + 1:
        return state  # new edge gives no shorter path to v
    region = _reachable_from(graph, n, v)
    region.discard(0)  # the root's distance is fixed at 0
    _recompute(graph, n, region, dist, parent)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state["parent"]
    dist = state["distances"]
    n = len(dist)
    if parent[v] != u:
        return state  # (u, v) is not v's tree edge: no tree path is lost
    region = _subtree_of(parent, n, v)
    region.discard(0)
    _recompute(graph, n, region, dist, parent)
    return state


def _full_bfs(graph, n, root):
    from collections import deque

    parent = [None] * n
    dist = [-1] * n
    dist[root] = 0
    q = deque([root])
    while q:
        u = q.popleft()
        row = graph[u]
        nd = dist[u] + 1
        for v in range(n):
            if row[v] == 1 and dist[v] == -1:
                dist[v] = nd
                parent[v] = u
                q.append(v)
    return parent, dist


def _reachable_from(graph, n, start):
    """All vertices reachable from start by following out-edges (incl. start)."""
    from collections import deque

    seen = {start}
    q = deque([start])
    while q:
        u = q.popleft()
        row = graph[u]
        for v in range(n):
            if row[v] == 1 and v not in seen:
                seen.add(v)
                q.append(v)
    return seen


def _subtree_of(parent, n, v):
    """v and all its descendants in the tree, found by walking parent chains."""
    region = set()
    for x in range(n):
        cur = x
        while cur is not None:
            if cur == v:
                region.add(x)
                break
            cur = parent[cur]
    return region


def _recompute(graph, n, region, dist, parent):
    """Recompute distances/parents for the vertices in region in place.

    Vertices outside region keep their current (final) distances. The new
    distance of a region vertex is the shortest path from the boundary (its
    in-neighbors outside region) into it, so a Dijkstra seeded from the
    boundary and relaxing only inside region is exact. The parent of each
    region vertex is the predecessor that achieves its best distance, tracked
    during the Dijkstra so no separate parent pass is needed.
    """
    best = {}
    par = {}
    heap = []
    for x in region:
        b = None
        for w in range(n):
            if graph[w][x] == 1 and w not in region and dist[w] != -1:
                cand = dist[w] + 1
                if b is None or cand < b:
                    b = cand
                    pb = w
        if b is not None:
            best[x] = b
            par[x] = pb
            heapq.heappush(heap, (b, x))

    final = {}
    while heap:
        d, w = heapq.heappop(heap)
        if w in final:
            continue
        final[w] = d
        row = graph[w]
        for x in range(n):
            if row[x] == 1 and x in region and x not in final:
                cand = d + 1
                if x not in best or cand < best[x]:
                    best[x] = cand
                    par[x] = w
                    heapq.heappush(heap, (cand, x))

    for x in region:
        if x in final:
            dist[x] = final[x]
            parent[x] = par[x]
        else:
            dist[x] = -1
            parent[x] = None
