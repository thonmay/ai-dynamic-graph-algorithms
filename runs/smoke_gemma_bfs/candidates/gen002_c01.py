def init(graph):
    n = len(graph)
    root = 0
    distances = [-1] * n
    parent = [None] * n
    
    distances[root] = 0
    queue = [root]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v in range(n):
            if graph[u][v] == 1 and distances[v] == -1:
                distances[v] = distances[u] + 1
                parent[v] = u
                queue.append(v)
                
    return {'distances': distances, 'parent': parent}

def insert_edge(graph, edge, state):
    u, v = edge
    dist_u = state['distances'][u]
    dist_v = state['distances'][v]
    
    # If u is unreachable or the new edge doesn't provide a shorter path, no change.
    if dist_u == -1 or (dist_v != -1 and dist_v <= dist_u + 1):
        return state
    
    # The edge (u, v) provides a shorter path to v.
    # We update v and potentially its descendants.
    n = len(graph)
    distances = list(state['distances'])
    parent = list(state['parent'])
    
    distances[v] = dist_u + 1
    parent[v] = u
    
    # BFS to propagate the distance decrease
    queue = [v]
    head = 0
    while head < len(queue):
        curr = queue[head]
        head += 1
        d_curr = distances[curr]
        for neighbor in range(n):
            if graph[curr][neighbor] == 1:
                if distances[neighbor] == -1 or distances[neighbor] > d_curr + 1:
                    distances[neighbor] = d_curr + 1
                    parent[neighbor] = curr
                    queue.append(neighbor)
                    
    return {'distances': distances, 'parent': parent}

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was not part of the BFS tree, no change.
    if state['parent'][v] != u:
        return state
    
    # If it was part of the tree, we need to check if v has another parent 
    # at the same distance.
    n = len(graph)
    distances = list(state['distances'])
    parent = list(state['parent'])
    
    # Try to find an alternative parent for v at the same distance
    found_alt = False
    for alt_u in range(n):
        if graph[alt_u][v] == 1 and distances[alt_u] == distances[v] - 1:
            parent[v] = alt_u
            found_alt = True
            break
            
    if found_alt:
        return {'distances': distances, 'parent': parent}
    
    # If no alternative parent at the same distance, v's distance increases.
    # This might trigger a cascade of distance increases.
    # For simplicity and correctness in the face of complex deletions, 
    # we recompute BFS when a tree edge is lost and no immediate replacement exists.
    return recompute_bfs(graph)

def recompute_bfs(graph):
    n = len(graph)
    root = 0
    distances = [-1] * n
    parent = [None] * n
    
    distances[root] = 0
    queue = [root]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v in range(n):
            if graph[u][v] == 1 and distances[v] == -1:
                distances[v] = distances[u] + 1
                parent[v] = u
                queue.append(v)
                
    return {'distances': distances, 'parent': parent}
