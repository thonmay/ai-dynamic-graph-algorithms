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
    # To avoid full recompute, we check if the new edge (u, v) 
    # creates a forward-cross edge.
    # A forward-cross edge is an edge (u, v) where discover[u] < discover[v]
    # but v is not a descendant of u in the current DFS tree.
    # However, for the calibration goal of "full correctness first",
    # and given the complexity of incremental DFS, we start by 
    # ensuring the recompute is robust.
    # The parent candidate used init(graph) which is correct.
    # We will implement a slightly more optimized recompute that 
    # doesn't recreate the state dict if not needed, but for now,
    # we stick to the proven correct logic.
    return init(graph)

def delete_edge(graph, edge, state):
    # If the deleted edge was not a tree edge, the DFS forest remains valid.
    u, v = edge
    if state['parent'][v] != u:
        return state
    
    # If it was a tree edge, we must recompute.
    return init(graph)
