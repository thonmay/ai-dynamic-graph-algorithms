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
    # If the new edge (u, v) provides a shorter path to v, we might need to update.
    # However, for a BFS tree, we only care if dist[u] + 1 < dist[v].
    # To keep it simple and correct while avoiding full recompute in some cases:
    # If dist[u] + 1 >= dist[v], the BFS tree structure doesn't necessarily change.
    # But to ensure full correctness and avoid complex logic, we check if the distance improves.
    
    dist_u = state['distances'][u]
    dist_v = state['distances'][v]
    
    if dist_u != -1 and (dist_v == -1 or dist_u + 1 < dist_v):
        # Distance to v improves, potentially triggering a cascade of updates.
        # We perform a limited BFS starting from v.
        n = len(graph)
        distances = list(state['distances'])
        parent = list(state['parent'])
        
        distances[v] = dist_u + 1
        parent[v] = u
        queue = deque([v])
        
        while queue:
            curr = queue.popleft()
            for neighbor in range(n):
                if graph[curr][neighbor] == 1:
                    if distances[neighbor] == -1 or distances[curr] + 1 < distances[neighbor]:
                        distances[neighbor] = distances[curr] + 1
                        parent[neighbor] = curr
                        queue.append(neighbor)
        return {'parent': parent, 'distances': distances}
    
    return state

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was not part of the BFS tree, no change is needed.
    if state['parent'][v] != u:
        return state
    
    # If it was part of the tree, v and its descendants might need new parents or distances.
    # For simplicity and guaranteed correctness in the dynamic case, 
    # we recompute from scratch when a tree edge is deleted.
    root = 0
    parent, distances = bfs(graph, root)
    return {'parent': parent, 'distances': distances}
