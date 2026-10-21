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
    # For a calibration problem, we start with a simple recomputation 
    # to ensure correctness, then optimize if needed.
    # However, the goal is to be dynamic. Let's implement a basic 
    # incremental update for BFS.
    u, v = edge
    dist_u = state['distances'][u]
    dist_v = state['distances'][v]
    
    # If u is unreachable or the new edge doesn't provide a shorter path, no change.
    if dist_u == -1 or dist_v != -1 and dist_v <= dist_u + 1:
        return state
    
    # If the edge provides a shorter path, we need to update v and its descendants.
    # To keep it simple and correct for this first candidate, we recompute.
    # The prompt says "start from the offline algorithm and make it dynamic".
    # A fully correct dynamic BFS is complex; recomputation is the baseline.
    return recompute_bfs(graph)

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was not part of the BFS tree, no change.
    if state['parent'][v] != u:
        return state
    
    # If it was part of the tree, we must recompute.
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
