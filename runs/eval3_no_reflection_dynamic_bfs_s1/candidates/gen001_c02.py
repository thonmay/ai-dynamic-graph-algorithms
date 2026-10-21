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
                
    return {'distances': distances, 'parent': parent}

def init(graph):
    return bfs(graph, 0)

def insert_edge(graph, edge, state):
    # For now, recompute to ensure correctness
    return bfs(graph, 0)

def delete_edge(graph, edge, state):
    # For now, recompute to ensure correctness
    return bfs(graph, 0)
