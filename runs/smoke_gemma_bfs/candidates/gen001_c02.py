from collections import deque

def bfs(graph, root):
    n = len(graph)
    distances = [-1] * n
    parent = [None] * n
    distances[root] = 0
    queue = deque([root])
    
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u][v] == 1 and distances[v] == -1:
                distances[v] = distances[u] + 1
                parent[v] = u
                queue.append(v)
    return parent, distances

def init(graph):
    root = 0
    parent, distances = bfs(graph, root)
    return {'parent': parent, 'distances': distances}

def insert_edge(graph, edge, state):
    # For a calibration problem, we start with a simple recomputation.
    # This ensures correctness while we establish the baseline.
    root = 0
    parent, distances = bfs(graph, root)
    return {'parent': parent, 'distances': distances}

def delete_edge(graph, edge, state):
    # For a calibration problem, we start with a simple recomputation.
    root = 0
    parent, distances = bfs(graph, root)
    return {'parent': parent, 'distances': distances}
