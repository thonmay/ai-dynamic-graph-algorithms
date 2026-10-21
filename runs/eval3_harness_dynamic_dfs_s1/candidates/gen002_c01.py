"""Dynamic algorithm candidate. Edit this file; keep the three functions."""

def run_dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [None] * n
    finish = [None] * n
    timer = 0
    
    visited = [False] * n
    
    # Using iterative DFS to avoid recursion limit and potentially slightly faster
    stack = [(0, 0)] # (node, neighbor_idx)
    visited[0] = True
    discover[0] = timer
    timer += 1
    
    while stack:
        u, idx = stack[-1]
        if idx < n:
            # Update current node's next neighbor to check
            stack[-1] = (u, idx + 1)
            v = idx
            if graph[u][v] and not visited[v]:
                visited[v] = True
                parent[v] = u
                discover[v] = timer
                timer += 1
                stack.append((v, 0))
        else:
            # All neighbors of u visited
            finish[u] = timer
            timer += 1
            stack.pop()
            
    return {'parent': parent, 'discover': discover, 'finish': finish}

def init(graph):
    return run_dfs(graph)

def insert_edge(graph, edge, state):
    return run_dfs(graph)

def delete_edge(graph, edge, state):
    return run_dfs(graph)
