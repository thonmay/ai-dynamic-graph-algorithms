"""Dynamic BFS tree from a fixed root (vertex 0) in a directed graph.

Insertion of (u, v) can only shorten distances, and only when
dist[u] + 1 < dist[v] (or v was unreachable): re-attach v under u and
propagate the decrease with a BFS that relaxes only shortening edges.
Deletion of a non-tree edge changes nothing (the tree still certifies
every distance). Deletion of the tree edge (u, v) re-attaches the
subtree under v in BFS order -- a vertex keeps its distance iff it has
a surviving in-neighbor one level up -- and re-reaches the lost
remainder from the surviving boundary with a Dijkstra pass.

Neighborhoods are kept as integer bitmasks so per-vertex work is a
constant number of big-int ops plus iteration over set bits.
"""

import heapq


def _bits(mask):
    while mask:
        lsb = mask & -mask
        yield lsb.bit_length() - 1
        mask ^= lsb


def _init_bfs(graph):
    n = len(graph)
    parent = [None] * n
    dist = [-1] * n
    dist[0] = 0
    queue = [0]
    for u in queue:
        nd = dist[u] + 1
        for v in range(n):
            if graph[u][v] and dist[v] == -1:
                dist[v] = nd
                parent[v] = u
                queue.append(v)
    return parent, dist


def _rebuild_children(parent):
    children = [[] for _ in parent]
    for v, p in enumerate(parent):
        if p is not None:
            children[p].append(v)
    return children


def init(graph):
    n = len(graph)
    parent, dist = _init_bfs(graph)
    out = [0] * n
    inn = [0] * n
    for u in range(n):
        row = graph[u]
        m = 0
        for v in range(n):
            if row[v]:
                m |= 1 << v
                inn[v] |= 1 << u
        out[u] = m
    levels = [0] * (n + 1)
    for v in range(n):
        if dist[v] != -1:
            levels[dist[v]] |= 1 << v
    return {"parent": parent, "distances": dist,
            "children": _rebuild_children(parent),
            "out": out, "inn": inn, "levels": levels}


def insert_edge(graph, edge, state):
    u, v = edge
    dist = state["distances"]
    out = state["out"]
    inn = state["inn"]
    out[u] |= 1 << v
    inn[v] |= 1 << u
    if dist[u] == -1 or (dist[v] != -1 and dist[u] + 1 >= dist[v]):
        return state
    parent = state["parent"]
    children = state["children"]
    levels = state["levels"]
    old = parent[v]
    if old is not None:
        children[old].remove(v)
    parent[v] = u
    levels[dist[v]] &= ~(1 << v)
    dist[v] = dist[u] + 1
    levels[dist[v]] |= 1 << v
    children[u].append(v)
    queue = [v]
    for x in queue:
        nd = dist[x] + 1
        for y in _bits(out[x]):
            dy = dist[y]
            if dy == -1:
                dist[y] = nd
                parent[y] = x
                levels[nd] |= 1 << y
                children[x].append(y)
                queue.append(y)
            elif dy > nd:
                children[parent[y]].remove(y)
                parent[y] = x
                levels[dy] &= ~(1 << y)
                dist[y] = nd
                levels[nd] |= 1 << y
                children[x].append(y)
                queue.append(y)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state["parent"]
    out = state["out"]
    inn = state["inn"]
    out[u] &= ~(1 << v)
    inn[v] &= ~(1 << u)
    if parent[v] != u:
        return state
    dist = state["distances"]
    n = len(graph)
    levels = state["levels"]
    # Subtree under v in BFS order (non-decreasing distance).
    subtree = []
    queue = [v]
    for x in queue:
        subtree.append(x)
        queue.extend(state["children"][x])
    lost = 0
    # Phase 1: in BFS order, a vertex keeps its distance iff it has a
    # surviving in-neighbor exactly one level up.
    for x in subtree:
        d = dist[x]
        cand = inn[x] & levels[d - 1] & ~lost
        if cand:
            parent[x] = (cand & -cand).bit_length() - 1
        else:
            lost |= 1 << x
            levels[d] &= ~(1 << x)
            dist[x] = -1
            parent[x] = None
    # Phase 2: lost vertices may still be reachable at a larger distance.
    if lost:
        best = {}
        par2 = {}
        heap = []
        for x in _bits(lost):
            bd = None
            bz = None
            for z in _bits(inn[x] & ~lost):
                if dist[z] == -1:
                    continue
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
            nd = d + 1
            for y in _bits(out[x] & lost):
                if y not in best or nd < best[y]:
                    best[y] = nd
                    par2[y] = x
                    heapq.heappush(heap, (nd, y))
        for x in _bits(lost):
            if x in best:
                dist[x] = best[x]
                parent[x] = par2[x]
                levels[best[x]] |= 1 << x
    state["children"] = _rebuild_children(parent)
    return state
