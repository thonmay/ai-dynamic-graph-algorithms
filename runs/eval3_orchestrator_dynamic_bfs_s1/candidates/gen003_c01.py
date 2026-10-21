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
    u, v = edge
    # If the new edge (u, v) provides a shorter path to v, we might update.
    # However, for a BFS tree, we only care if dist[u] + 1 < dist[v].
    # To avoid full recompute, we can start a BFS from v if its distance decreases.
    
    dist_u = state['distances'][u]
    dist_v = state['distances'][v]
    
    if dist_u != -1 and (dist_v == -1 or dist_u + 1 < dist_v):
        # Distance to v decreases. This might trigger a cascade of updates.
        n = len(graph)
        distances = list(state['distances'])
        parent = list(state['parent'])
        
        distances[v] = dist_u + 1
        parent[v] = u
        
        queue = deque([v])
        while queue:
            curr = queue.popleft()
            d_curr = distances[curr]
            for neighbor in range(n):
                if graph[curr][neighbor] == 1:
                    if distances[neighbor] == -1 or d_curr + 1 < distances[neighbor]:
                        distances[neighbor] = d_curr + 1
                        parent[neighbor] = curr
                        queue.append(neighbor)
        return {'parent': parent, 'distances': distances}
    
    return state

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge (u, v) was not part of the BFS tree, no change.
    if state['parent'][v] != u:
        return state
    
    # If it was part of the tree, v and its descendants might need new parents.
    # For simplicity and correctness in this step, we recompute.
    # A more optimized version would identify the affected subtree.
    root = 0
    parent, distances = bfs(graph, root)
    return {'parent': parent, 'distances': distances}
