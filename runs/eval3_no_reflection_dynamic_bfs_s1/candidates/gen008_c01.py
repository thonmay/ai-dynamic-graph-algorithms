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
    
    # If u is unreachable or the new edge doesn't shorten the path to v, no change.
    if dist_u == -1 or (dist_v != -1 and dist_u + 1 >= dist_v):
        return state
    
    # Distance to v improves, potentially triggering a cascade of updates.
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

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was not part of the BFS tree, no change is needed.
    if state['parent'][v] != u:
        return state
    
    # If it was part of the tree, v and its descendants might need new parents or distances.
    # Instead of full recompute, we identify the affected subtree and try to re-attach.
    n = len(graph)
    distances = list(state['distances'])
    parent = list(state['parent'])
    
    # Identify all nodes in the subtree rooted at v in the BFS tree.
    affected = set()
    stack = [v]
    while stack:
        curr = stack.pop()
        affected.add(curr)
        for i in range(n):
            if parent[i] == curr:
                stack.append(i)
    
    # Reset distances and parents for the affected subtree.
    for node in affected:
        distances[node] = -1
        parent[node] = None
    
    # Try to find new parents for affected nodes from non-affected nodes.
    # We use a priority queue (or just sorted levels) to process nodes in BFS order.
    # Since we only have a few levels, we can just iterate.
    
    # Initial candidates for re-attachment: affected nodes that have an edge from a non-affected node.
    queue = deque()
    
    # To maintain BFS property, we must process nodes in increasing order of distance.
    # We can find all affected nodes that can be reached from the remaining BFS tree.
    # The remaining tree is everything not in 'affected'.
    
    # Find all nodes in 'affected' that have an in-neighbor not in 'affected'
    # and whose distance would be min(dist[in_neighbor] + 1).
    
    # To be safe and efficient, we can just run a BFS starting from the boundary.
    # The boundary consists of all nodes u not in 'affected' such that there is an edge (u, w) with w in 'affected'.
    
    boundary_queue = deque()
    # We need to process the boundary in order of distance.
    # Collect all nodes not in 'affected' and sort them by distance.
    non_affected = [i for i in range(n) if i not in affected]
    non_affected.sort(key=lambda x: distances[x])
    
    for u in non_affected:
        if distances[u] == -1: continue
        for w in range(n):
            if graph[u][w] == 1 and w in affected:
                if distances[w] == -1 or distances[u] + 1 < distances[w]:
                    distances[w] = distances[u] + 1
                    parent[w] = u
                    # We don't add to boundary_queue yet, we process all non-affected first
                    # to find the absolute minimum distance for the first layer of affected.
    
    # Now we have the first layer of the affected subtree re-attached.
    # We can now run a standard BFS starting from these newly attached nodes.
    # First, collect all nodes in 'affected' that now have a distance.
    start_nodes = [w for w in affected if distances[w] != -1]
    start_nodes.sort(key=lambda x: distances[x])
    
    queue = deque(start_nodes)
    while queue:
        curr = queue.popleft()
        for neighbor in range(n):
            if graph[curr][neighbor] == 1:
                if distances[neighbor] == -1 or distances[curr] + 1 < distances[neighbor]:
                    distances[neighbor] = distances[curr] + 1
                    parent[neighbor] = curr
                    queue.append(neighbor)
                    
    return {'parent': parent, 'distances': distances}
