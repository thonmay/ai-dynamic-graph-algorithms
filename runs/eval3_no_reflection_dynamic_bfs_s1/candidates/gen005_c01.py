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
    dist_u = state['distances'][u]
    dist_v = state['distances'][v]
    
    # If u is unreachable, the new edge (u, v) cannot improve v's distance.
    if dist_u == -1:
        return state
        
    # If the new edge provides a shorter path to v, we update and propagate.
    if dist_v == -1 or dist_u + 1 < dist_v:
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
    # If the deleted edge was not part of the BFS tree, no change is needed.
    if state['parent'][v] != u:
        return state
    
    # If it was part of the tree, we need to check if v can find another parent at the same distance.
    n = len(graph)
    distances = list(state['distances'])
    parent = list(state['parent'])
    
    # Try to find an alternative parent for v that maintains its distance.
    found_alt = False
    dist_v = distances[v]
    for potential_p in range(n):
        if graph[potential_p][v] == 1 and distances[potential_p] == dist_v - 1:
            parent[v] = potential_p
            found_alt = True
            break
            
    if found_alt:
        # Distance of v didn't change, so descendants' distances might not change.
        # However, we must ensure the BFS tree property is maintained.
        # In a BFS tree, any edge (x, y) must satisfy dist(y) <= dist(x) + 1.
        # Since dist(v) is unchanged, the distances of all nodes remain valid.
        return {'parent': parent, 'distances': distances}
    
    # If no alternative parent at the same distance, v's distance increases or it becomes unreachable.
    # To maintain correctness simply, we recompute from the root.
    root = 0
    parent, distances = bfs(graph, root)
    return {'parent': parent, 'distances': distances}
