"""Dynamic BFS tree maintenance from a fixed root (vertex 0).

State is a dict with:
  - 'parent': list, parent[root]=None, parent[v]=None if unreachable
  - 'distances': list, distances[v] = BFS distance from root, -1 if unreachable

Only the affected region is repaired after each update, so a single edge
flip costs well below a full recompute.
"""

from collections import deque


def _bfs(graph):
    """Full BFS from root 0. Returns (parent, distances)."""
    n = len(graph)
    distances = [-1] * n
    parent = [None] * n
    distances[0] = 0
    q = deque([0])
    while q:
        x = q.popleft()
        dx = distances[x]
        row = graph[x]
        for y in range(n):
            if row[y] == 1 and distances[y] == -1:
                distances[y] = dx + 1
                parent[y] = x
                q.append(y)
    return parent, distances


def init(graph):
    parent, distances = _bfs(graph)
    return {"parent": parent, "distances": distances}


def _propagate_decrease(graph, state, start):
    """Relax distances outward from `start` (whose distance just dropped or
    became reachable). Adding an edge can only decrease distances, so a
    shortest-path relaxation over out-neighbors is sufficient and correct."""
    n = len(graph)
    distances = state["distances"]
    parent = state["parent"]
    q = deque([start])
    while q:
        x = q.popleft()
        dx = distances[x]
        row = graph[x]
        for y in range(n):
            if row[y] == 1:
                dy = distances[y]
                if dy == -1 or dx + 1 < dy:
                    distances[y] = dx + 1
                    parent[y] = x
                    q.append(y)


def insert_edge(graph, edge, state):
    u, v = edge
    distances = state["distances"]
    parent = state["parent"]
    du = distances[u]
    if du == -1:
        # u unreachable: an edge out of it helps nobody.
        return state
    nd = du + 1
    if distances[v] == -1 or nd < distances[v]:
        # distances[v] == -1 (newly reachable) or a genuine decrease.
        distances[v] = nd
        parent[v] = u
        _propagate_decrease(graph, state, v)
    # otherwise the edge does not improve any distance: no repair needed.
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    distances = state["distances"]
    parent = state["parent"]

    if parent[v] != u:
        # The deleted edge was not v's tree edge, so v (and everyone else)
        # still has a valid parent one level closer. Nothing changes.
        return state

    # v lost its tree edge. Look for another in-neighbor one level closer.
    dv = distances[v]
    alt = None
    for w in range(n):
        if graph[w][v] == 1 and distances[w] == dv - 1:
            alt = w
            break
    if alt is not None:
        parent[v] = alt
        return state

    # No local replacement: v's distance must rise (or it becomes
    # unreachable). Only v's subtree in the BFS tree can be affected, so
    # recompute exactly that region.
    children = [[] for _ in range(n)]
    for x in range(n):
        p = parent[x]
        if p is not None:
            children[p].append(x)

    # S = v and all its descendants in the current BFS tree.
    inS = [False] * n
    stack = [v]
    inS[v] = True
    while stack:
        x = stack.pop()
        for c in children[x]:
            if not inS[c]:
                inS[c] = True
                stack.append(c)

    # New distances for S: shortest path where vertices outside S keep their
    # (unchanged) distance. Unit weights -> Dijkstra over the tiny region.
    INF = float("inf")
    d = {}
    for x in range(n):
        if inS[x]:
            d[x] = INF
    for x in range(n):
        if inS[x]:
            best = INF
            for y in range(n):
                if not inS[y] and graph[y][x] == 1 and distances[y] != -1:
                    cand = distances[y] + 1
                    if cand < best:
                        best = cand
            d[x] = best

    import heapq
    heap = []
    for x in range(n):
        if inS[x] and d[x] < INF:
            heapq.heappush(heap, (d[x], x))
    while heap:
        dist, x = heapq.heappop(heap)
        if dist > d[x]:
            continue
        row = graph[x]
        for z in range(n):
            if inS[z] and row[z] == 1:
                nd = dist + 1
                if nd < d[z]:
                    d[z] = nd
                    heapq.heappush(heap, (nd, z))

    for x in range(n):
        if inS[x]:
            if d[x] == INF:
                distances[x] = -1
                parent[x] = None
            else:
                distances[x] = d[x]
                newp = None
                for y in range(n):
                    if graph[y][x] == 1:
                        dy = d[y] if inS[y] else distances[y]
                        if dy != -1 and dy + 1 == d[x]:
                            newp = y
                            break
                parent[x] = newp
    return state
