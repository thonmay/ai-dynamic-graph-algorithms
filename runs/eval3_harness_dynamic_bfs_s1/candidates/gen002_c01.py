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
    # Only matters if (u, v) was the parent edge of v.
    if state["parent"][v] != u:
        return state
        
    # v and its descendants might be affected.
    # To be safe and correct, we can recompute. But the goal is to avoid full recompute.
    # In a small graph, we can find all descendants and check if they have other parents at the same distance.
    
    n = len(graph)
    distances = list(state["distances"])
    parent = list(state["parent"])
    
    # Find all descendants of v in the BFS tree.
    descendants = []
    stack = [v]
    visited = {v}
    while stack:
        curr = stack.pop()
        descendants.append(curr)
        for i in range(n):
            if parent[i] == curr:
                stack.append(i)
                visited.add(i)
    
    # For each descendant, try to find a new parent that maintains its distance.
    # This is tricky for a general directed graph. 
    # To ensure correctness first, we'll do a targeted re-BFS for affected nodes.
    # But actually, the simplest correct dynamic BFS for deletion is to mark 
    # descendants as -1 and then try to re-attach them.
    
    for d in descendants:
        distances[d] = -1
        parent[d] = None
        
    # Try to re-attach nodes that have a neighbor with distance < current? 
    # No, just re-run BFS from root, but we can optimize by starting from the frontier.
    # For now, let's use a full BFS for deletions to ensure correctness, 
    # then optimize once we have a working a-priori structure.
    # Wait, I already have a recompute in the first version. 
    # Let's try a simple "recompute all" for delete_edge for now, and "incremental" for insert_edge.
    
    return bfs(graph)
