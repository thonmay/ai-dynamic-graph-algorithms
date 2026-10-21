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
    u, v = edge
    # Root is 0.
    # If v was already reachable, its distance cannot decrease unless u's distance + 1 < v's distance.
    # However, the simplest dynamic update is: if distances[v] > distances[u] + 1, update v and its descendants.
    
    dist_u = state["distances"][u]
    dist_v = state["distances"][v]
    
    if dist_u == -1 or dist_v != -1 and dist_v <= dist_u + 1:
        return state # No change to BFS distance or tree structure
        
    # v's distance improves. Start a BFS from v.
    n = len(graph)
    distances = list(state["distances"])
    parent = list(state["parent"])
    
    distances[v] = dist_u + 1
    parent[v] = u
    queue = deque([v])
    
    while queue:
        curr = queue.popleft()
        for neighbor in range(n):
            if graph[curr][neighbor]:
                if distances[neighbor] == -1 or distances[neighbor] > distances[curr] + 1:
                    distances[neighbor] = distances[curr] + 1
                    parent[neighbor] = curr
                    queue.append(neighbor)
                    
    return {"distances": distances, "parent": parent}

def delete_edge(graph, edge, state):
    u, v = edge
    if state["parent"][v] != u:
        return state
        
    n = len(graph)
    # Find descendants of v in the BFS tree
    descendants = []
    stack = [v]
    visited = {v}
    while stack:
        curr = stack.pop()
        descendants.append(curr)
        for i in range(n):
            if state["parent"][i] == curr:
                stack.append(i)
                visited.add(i)
    
    distances = list(state["distances"])
    parent = list(state["parent"])
    
    # Mark descendants as unreachable
    for d in descendants:
        distances[d] = -1
        parent[d] = None
        
    # Use a simplified Ramalingam-Reps approach:
    # Only re-process nodes that were descendants.
    # Start BFS from all non-descendants that have edges into descendants.
    
    q = deque()
    # Find all existing edges (non-descendant -> descendant)
    for i in range(n):
        if i not in visited and distances[i] != -1:
            for d in descendants:
                if graph[i][d]:
                    # Potential new parent. We don't add to q yet 
                    # because we need to process in distance order.
                    pass
    
    # The simplest correct way to optimize this for small n is to use 
    # the existing distances of non-affected nodes as the starting frontier.
    
    sorted_frontier = sorted([i for i in range(n) if i not in visited and distances[i] != -1], 
                             key=lambda x: distances[x])
    q = deque(sorted_frontier)
    
    # Since we already set distances of descendants to -1, 
    # this is just a BFS that only fills in the holes.
    
    # To ensure we don't change distances of non-descendants, 
    # we only update if distances[neighbor] == -1 (which it is for descendants).
    
    while q:
        curr = q.popleft()
        for neighbor in range(n):
            if graph[curr][neighbor] and distances[neighbor] == -1:
                distances[neighbor] = distances[curr] + 1
                parent[neighbor] = curr
                q.append(neighbor)
                
    return {"distances": distances, "parent": parent}
