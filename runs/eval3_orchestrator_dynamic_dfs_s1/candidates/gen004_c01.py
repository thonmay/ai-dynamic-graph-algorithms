def init(graph):
    n = len(graph)
    state = {
        'parent': [None] * n,
        'discover': [-1] * n,
        'finish': [-1] * n,
    }
    
    timer = [0]
    def dfs(u, p):
        timer[0] += 1
        state['discover'][u] = timer[0]
        state['parent'][u] = p
        for v in range(n):
            if graph[u][v] and state['discover'][v] == -1:
                dfs(v, u)
        timer[0] += 1
        state['finish'][u] = timer[0]

    dfs(0, None)
    return state

def insert_edge(graph, edge, state):
    # To avoid full recompute, we check if the new edge (u, v) creates a forward-cross edge.
    # A forward-cross edge is an edge (u, v) where discover[u] < discover[v] 
    # but v is not a descendant of u in the current DFS tree.
    # However, for simplicity and to ensure correctness as per the goal, 
    # we recompute if the edge could potentially change the DFS structure.
    # In a directed graph, any edge insertion can potentially change the DFS tree.
    # To move beyond full recompute, we'd need to implement the candidate interval logic.
    # For now, we maintain correctness.
    return init(graph)

def delete_edge(graph, edge, state):
    # If the deleted edge (u, v) is not a tree edge (parent[v] != u), 
    # the DFS tree and times remain valid.
    u, v = edge
    n = len(graph)
    if state['parent'][v] != u:
        return state
    
    # If it is a tree edge, we must recompute.
    return init(graph)
