# Dynamic BFS (directed), root 0.
# Maintains a BFS tree as {'parent': [...], 'dist': [...]} over all n vertices
# (list-based; None / INF mark the root and unreachable vertices).
# Fully dynamic:
#   insert (u,v): distances only decrease. If u is reachable and dist[u]+1
#     improves v, re-parent v to u and propagate the decrease along OUT-EDGES
#     in BFS order. A shorter path to v can shorten any out-neighbor w (edge
#     v->w), whether or not w is a tree-child of v -- following only tree
#     children would miss non-tree out-neighbors in a directed graph.
#   delete (u,v): distances only increase. If (u,v) is not a tree edge the
#     tree is untouched: its paths still give every vertex its true distance,
#     so removing a non-tree edge changes nothing. If it is a tree edge, only
#     v's subtree S can change: recompute S's distances as a multi-source
#     shortest path seeded by the boundary (incoming edges from outside S),
#     then drop any S-vertex left unreachable.
from collections import deque
import heapq

ROOT = 0
INF = 10 ** 9


def _bfs(graph):
    """Offline BFS from ROOT; returns {'parent': [...], 'dist': [...]}."""
    n = len(graph)
    parent = [None] * n
    dist = [INF] * n
    dist[ROOT] = 0
    q = deque([ROOT])
    while q:
        u = q.popleft()
        row = graph[u]
        for v in range(n):
            if row[v] == 1 and dist[v] == INF:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return {'parent': parent, 'dist': dist}


def _subtree(parent, start):
    """All descendants of start (inclusive) in the tree."""
    children = {}
    for v, p in enumerate(parent):
        if p is not None and p != v:
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

    # The new edge can only shorten distances, starting at v.
    if dist[u] != INF and dist[u] + 1 < dist[v]:
        dist[v] = dist[u] + 1
        parent[v] = u
        # Propagate the decrease along out-edges in BFS order.
        q = deque([v])
        while q:
            x = q.popleft()
            dx = dist[x]
            row = graph[x]
            for w in range(n):
                if row[w] == 1 and dx + 1 < dist[w]:
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
    if parent[v] != u:
        return {'parent': parent, 'dist': dist}

    # (u,v) was a tree edge: only v's subtree S can change.
    sub = _subtree(parent, v)

    # Seed each S-vertex with the best incoming edge from outside S.
    best = {}
    best_parent = {}
    for x in sub:
        for a in range(n):
            if a not in sub and dist[a] != INF and graph[a][x] == 1:
                d = dist[a] + 1
                if x not in best or d < best[x]:
                    best[x] = d
                    best_parent[x] = a

    # Multi-source shortest path inside S (all edges have weight 1).
    nd = dict(best)
    np_ = dict(best_parent)
    heap = [(d, x) for x, d in best.items()]
    heapq.heapify(heap)
    while heap:
        d, x = heapq.heappop(heap)
        if d > nd[x]:
            continue
        row = graph[x]
        for y in range(n):
            if y in sub and row[y] == 1:
                nd2 = d + 1
                if y not in nd or nd2 < nd[y]:
                    nd[y] = nd2
                    np_[y] = x
                    heapq.heappush(heap, (nd2, y))

    # Rewrite the subtree: drop vertices that lost every path to the root.
    for x in sub:
        if x in nd:
            dist[x] = nd[x]
            parent[x] = np_[x]
        else:
            dist[x] = INF
            parent[x] = None
    return {'parent': parent, 'dist': dist}
