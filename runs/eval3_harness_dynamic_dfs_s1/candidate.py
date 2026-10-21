"""Dynamic algorithm candidate. Edit this file; keep the three functions."""

def run_dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [None] * n
    finish = [None] * n
    timer = 0
    
    visited = [False] * n
    stack = [(0, 0)] 
    visited[0] = True
    discover[0] = timer
    timer += 1
    
    while stack:
        u, idx = stack[-1]
        if idx < n:
            stack[-1] = (u, idx + 1)
            v = idx
            if graph[u][v] and not visited[v]:
                visited[v] = True
                parent[v] = u
                discover[v] = timer
                timer += 1
                stack.append((v, 0))
        else:
            finish[u] = timer
            timer += 1
            stack.pop()
            
    return {'parent': parent, 'discover': discover, 'finish': finish}

def init(graph):
    return run_dfs(graph)

def insert_edge(graph, edge, state):
    u, v = edge
    # If the edge is already present (shouldn't happen per rules but for safety)
    # or if it doesn't change reachability/structure of the DFS tree, we could skip.
    # However, Yang et al. Lemma 1: a tree is DFS iff no forward-cross edges.
    # An insertion u->v can create a forward-cross edge if discover[u] < discover[v]
    # and v is NOT a descendant of u.
    
    p = state['parent']
    disc = state['discover']
    
    if disc[u] is None or disc[v] is None:
        return run_dfs(graph)
    
    # Check if v is descendant of u
    is_descendant = False
    curr = v
    while curr is not None:
        if curr == u:
            is_descendant = True
            break
        curr = p[curr]
    
    if disc[u] < disc[v] and not is_descendant:
        # Created a forward-cross edge
        return run_dfs(graph)
    
    # Otherwise, the current DFS tree remains a valid DFS tree.
    # We just need to ensure discovery/finish times are consistent.
    # Since the tree structure is the same, discovery/finish times stay the same.
    return state

def delete_edge(graph, edge, state):
    u, v = edge
    p = state['parent']
    # If (u, v) was a tree edge, we must recompute.
    if p[v] == u:
        return run_dfs(graph)
    
    # If it was a back/forward/cross edge, the DFS tree structure is unchanged.
    return state
