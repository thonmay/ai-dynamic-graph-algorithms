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
    u, v = edge
    n = len(graph)
    
    # If v is not reachable from root, or if u is not reachable, 
    # the edge might change reachability or the DFS structure.
    # If v is already reachable, we check if (u, v) is a forward-cross edge.
    # A forward-cross edge is u -> v where discover[u] < discover[v] 
    # but v is not a descendant of u.
    
    # To be safe and correct for the calibration, we check if the edge 
    # violates the DFS property: for every edge u->v, either:
    # 1. v is a descendant of u (discover[u] < discover[v] < finish[v] < finish[u])
    # 2. u is a descendant of v (discover[v] < discover[u] < finish[u] < finish[v])
    # 3. v was finished before u was discovered (finish[v] < discover[u])
    
    if state['discover'][u] == -1 or state['discover'][v] == -1:
        # One of them is unreachable; reachability might change.
        return init(graph)
    
    # Check if the new edge (u, v) is a forward-cross edge.
    # If discover[u] < discover[v], v must be a descendant of u.
    if state['discover'][u] < state['discover'][v]:
        # Check if v is a descendant of u
        if not (state['discover'][u] < state['discover'][v] < state['finish'][v] < state['finish'][u]):
            return init(graph)
            
    # If it's a back edge or a cross edge (finish[v] < discover[u]), it's fine.
    return state

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was not a tree edge, the DFS forest remains valid.
    # A tree edge is one where parent[v] == u.
    if state['parent'][v] != u:
        return state
    
    # If it was a tree edge, we must recompute.
    return init(graph)
