# dynamic_bfs (directed): maintain a BFS tree from root 0.
# Naive approach: recompute BFS from scratch on every update.
from collections import deque

ROOT = 0  # problem parameter: BFS tree rooted at vertex 0


def _bfs(graph):
    """Return a BFS tree from ROOT as {'parent': {...}, 'dist': {...}}."""
    n = len(graph)
    dist = {ROOT: 0}
    parent = {}
    q = deque([ROOT])
    while q:
        u = q.popleft()
        for v in range(n):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    return {'parent': parent, 'dist': dist}


def init(graph):
    return _bfs(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    graph[u][v] = 1  # idempotent: apply the insert in place before recomputing
    return _bfs(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    graph[u][v] = 0  # idempotent: apply the delete in place before recomputing
    return _bfs(graph)
