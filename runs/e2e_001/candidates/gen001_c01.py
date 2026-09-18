# Dynamic BFS (directed), root 0.
# Maintains a BFS tree as {'parent': {v: p}, 'dist': {v: d}} over reachable
# vertices only. Fully dynamic: an update touches only the affected subtree.
#   insert (u,v): distances only decrease. If d[u]+1 improves d[v], re-parent
#     v to u and cascade the improvement down v's tree. The tree path from v
#     to any descendant is the shortest v->descendant path (else the old BFS
#     would have used it), so following tree edges yields exact new distances.
#   delete (u,v): distances only increase. If (u,v) is not a tree edge the
#     tree is unchanged. If it is, recompute v's subtree with a multi-source
#     Dijkstra seeded by the subtree boundary (incoming edges from outside);
#     Dijkstra (not plain BFS) because a vertex's best entry may come via a
#     different boundary node than its own direct boundary edge.
from collections import deque
import heapq

ROOT = 0


def _bfs(graph):
    """Offline BFS from ROOT; returns {'parent': {...}, 'dist': {...}}."""
    n = len(graph)
    dist = {ROOT: 0}
    parent = {ROOT: None}
    q = deque([ROOT])
    while q:
        u = q.popleft()
        du = dist[u]
        row = graph[u]
        for v in range(n):
            if row[v] == 1 and v not in dist:
                dist[v] = du + 1
                parent[v] = u
                q.append(v)
    return {'parent': parent, 'dist': dist}


def _subtree(parent, start):
    """All descendants of start (inclusive) in the tree."""
    children = {}
    for v, p in parent.items():
        if p is not None:
            children.setdefault(p, []).append(v)
    seen = {start}
    q = deque([start])
    while q:
        u = q.popleft()
        for w in children.get(u, ()):
            if w not in seen:
                seen.add(w)
                q.append(w)
    return seen


def init(graph):
    return _bfs(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    dist = state['dist']

    # The new edge can only shorten v's distance (and v's descendants').
    if u in dist:
        cand = dist[u] + 1
        if v not in dist or cand < dist[v]:
            dist[v] = cand
            parent[v] = u
            # Cascade the improvement down v's tree in BFS order.
            q = deque([v])
            while q:
                x = q.popleft()
                dx = dist[x]
                for w in range(n):
                    if parent.get(w) == x and dx + 1 < dist.get(w, 1 << 62):
                        dist[w] = dx + 1
                        parent[w] = x
                        q.append(w)
    return {'parent': parent, 'dist': dist}


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    parent = state['parent']
    dist = state['dist']

    # A non-tree edge never changes the BFS tree.
    if parent.get(v) != u:
        return {'parent': parent, 'dist': dist}

    # (u,v) was a tree edge: recompute v's subtree from the boundary.
    sub = _subtree(parent, v)

    # Seed each subtree vertex with the best incoming edge from outside.
    best = {}
    best_parent = {}
    for x in sub:
        for a in range(n):
            if a not in sub and a in dist and graph[a][x] == 1:
                d = dist[a] + 1
                if x not in best or d < best[x]:
                    best[x] = d
                    best_parent[x] = a

    # Multi-source Dijkstra inside the subtree (all edges have weight 1).
    nd = dict(best)
    np_ = dict(best_parent)
    heap = [(d, x) for x, d in best.items()]
    heapq.heapify(heap)
    while heap:
        d, x = heapq.heappop(heap)
        if d > nd[x]:
            continue
        for y in range(n):
            if y in sub and graph[x][y] == 1:
                nd2 = d + 1
                if y not in nd or nd2 < nd[y]:
                    nd[y] = nd2
                    np_[y] = x
                    heapq.heappush(heap, (nd2, y))

    # Drop subtree vertices that lost every path to the root.
    for x in list(parent):
        if x in sub and x not in nd:
            del parent[x]
            del dist[x]
    for x in nd:
        dist[x] = nd[x]
        parent[x] = np_[x]
    return {'parent': parent, 'dist': dist}
