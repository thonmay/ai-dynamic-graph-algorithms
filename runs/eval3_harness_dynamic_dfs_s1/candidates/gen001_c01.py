"""Dynamic algorithm candidate. Edit this file; keep the three functions."""

def run_dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [None] * n
    finish = [None] * n
    timer = 0
    
    visited = [False] * n
    
    def visit(u):
        nonlocal timer
        visited[u] = True
        discover[u] = timer
        timer += 1
        for v in range(n):
            if graph[u][v] and not visited[v]:
                parent[v] = u
                visit(v)
        finish[u] = timer
        timer += 1

    visit(0)
    return {'parent': parent, 'discover': discover, 'finish': finish}

def init(graph):
    return run_dfs(graph)

def insert_edge(graph, edge, state):
    return run_dfs(graph)

def delete_edge(graph, edge, state):
    return run_dfs(graph)
