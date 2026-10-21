"""Dynamic algorithm candidate. Edit this file; keep the three functions."""
from collections import deque

def bfs(graph):
    n = len(graph)
    distances = [-1] * n
    parent = [None] * n
    distances[0] = 0
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] and distances[v] == -1:
                distances[v] = distances[u] + 1
                parent[v] = u
                queue.append(v)
    return {"distances": distances, "parent": parent}

def init(graph):
    return bfs(graph)

def insert_edge(graph, edge, state):
    return bfs(graph)

def delete_edge(graph, edge, state):
    return bfs(graph)
