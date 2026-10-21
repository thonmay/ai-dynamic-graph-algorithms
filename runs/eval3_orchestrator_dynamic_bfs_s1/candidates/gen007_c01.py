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
    
    # If the new edge (u, v) provides a shorter path to v, update and propagate.
    if dist_u != -1 and (dist_v == -1 or dist_u + 1 < dist_v):
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
    # We identify the affected subtree and try to re-attach nodes.
    n = len(graph)
    distances = list(state['distances'])
    parent = list(state['parent'])
    
    # Find all descendants of v in the BFS tree
    affected = []
    stack = [v]
    while stack:
        curr = stack.pop()
        affected.append(curr)
        for i in range(n):
            if parent[i] == curr:
                stack.append(i)
    
    # Reset affected nodes
    for node in affected:
        distances[node] = -1
        parent[node] = None
    
    # Try to re-attach affected nodes using edges from non-affected nodes
    # We use a queue to process nodes in increasing order of distance
    queue = deque()
    
    # Initial candidates for re-attachment: nodes in 'affected' that have an edge from a non-affected node
    # with distance d such that d + 1 is the new distance.
    # Actually, a simpler way is to run a BFS starting from the boundary.
    
    # Find all nodes that are NOT affected but have an edge to an affected node
    for i in range(n):
        if i not in affected and distances[i] != -1:
            for j in range(n):
                if graph[i][j] == 1 and j in affected:
                    # Potential new parent for j
                    if distances[j] == -1 or distances[i] + 1 < distances[j]:
                        distances[j] = distances[i] + 1
                        parent[j] = i
                        queue.append(j)
    
    # Standard BFS to propagate updates through the affected set
    # Since we want the shortest path, we should process the queue in distance order.
    # Because the boundary nodes might have different distances, we use a priority queue or 
    # just sort the initial queue.
    
    # To keep it simple and correct, we can just use a BFS starting from all root-reachable nodes.
    # But to avoid full recompute, we only start from the boundary.
    
    # Sort initial queue by distance to ensure BFS property
    sorted_initial = sorted(list(queue), key=lambda x: distances[x])
    queue = deque(sorted_initial)
    
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
