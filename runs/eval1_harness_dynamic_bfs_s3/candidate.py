"""Dynamic BFS tree from a fixed root (vertex 0) in a directed graph.

Insertion of (u, v) can only shorten distances, and only when
dist[u] + 1 < dist[v] (or v was unreachable): re-attach v under u and
propagate the decrease with a BFS that relaxes only shortening edges.
Deletion of a non-tree edge changes nothing (the tree still certifies
every distance). Deletion of the tree edge (u, v) re-attaches the
subtree under v in BFS order -- a vertex keeps its distance iff it has
a surviving in-neighbor one level up -- and re-reaches the lost
remainder from the surviving boundary with a Dijkstra pass.

The child lists of the tree are built during the initial BFS and kept
current incrementally, so no update ever rebuilds them.
"""

import heapq


def init(graph):
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    children = [[] for _ in range(n)]
    dist[0] = 0
    queue = [0]
    for u in queue:
        row = graph[u]
        nd = dist[u] + 1
        for v in range(n):
            if row[v] and dist[v] == -1:
                dist[v] = nd
                parent[v] = u
                children[u].append(v)
                queue.append(v)
    return {"parent": parent, "distances": dist, "children": children}


def insert_edge(graph, edge, state):
    u, v = edge
    dist = state["distances"]
    if dist[u] == -1 or (dist[v] != -1 and dist[u] + 1 >= dist[v]):
        return state
    parent = state["parent"]
    children = state["children"]
    old = parent[v]
    if old is not None:
        children[old].remove(v)
    parent[v] = u
    dist[v] = dist[u] + 1
    children[u].append(v)
    n = len(graph)
    queue = [v]
    for x in queue:
        row = graph[x]
        nd = dist[x] + 1
        for y in range(n):
            if not row[y]:
                continue
            dy = dist[y]
            if dy == -1:
                dist[y] = nd
                parent[y] = x
                children[x].append(y)
                queue.append(y)
            elif dy > nd:
                children[parent[y]].remove(y)
                parent[y] = x
                dist[y] = nd
                children[x].append(y)
                queue.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state["parent"]
    if parent[v] != u:
        return state
    dist = state["distances"]
    n = len(graph)
    children = state["children"]
    # Subtree under v in BFS order (non-decreasing distance).
    subtree = []
    queue = [v]
    for x in queue:
        subtree.append(x)
        queue.extend(children[x])
    lost = set()
    # Phase 1: in BFS order, a vertex keeps its distance iff it has a
    # surviving in-neighbor exactly one level up. Lost vertices carry
    # dist -1, so the level test alone excludes them.
    for x in subtree:
        dx = dist[x]
        old_p = parent[x]
        kept = False
        for z in range(n):
            if graph[z][x] and dist[z] + 1 == dx:
                if z != old_p:
                    parent[x] = z
                    children[old_p].remove(x)
                    children[z].append(x)
                kept = True
                break
        if not kept:
            lost.add(x)
            dist[x] = -1
            parent[x] = None
            children[old_p].remove(x)
    # Phase 2: lost vertices may still be reachable at a larger distance.
    if lost:
        best = {}
        par2 = {}
        heap = []
        for x in lost:
            bd = None
            bz = None
            for z in range(n):
                if graph[z][x] and dist[z] != -1:
                    d = dist[z] + 1
                    if bd is None or d < bd:
                        bd = d
                        bz = z
            if bd is not None:
                best[x] = bd
                par2[x] = bz
                heap.append((bd, x))
        heapq.heapify(heap)
        while heap:
            d, x = heapq.heappop(heap)
            if d != best.get(x):
                continue
            row = graph[x]
            nd = d + 1
            for y in range(n):
                if row[y] and y in lost and (y not in best or nd < best[y]):
                    best[y] = nd
                    par2[y] = x
                    heapq.heappush(heap, (nd, y))
        for x in lost:
            if x in best:
                dist[x] = best[x]
                parent[x] = par2[x]
                children[par2[x]].append(x)
    return state
