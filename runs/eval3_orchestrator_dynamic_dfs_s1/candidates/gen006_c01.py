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
    # but v is not a descendant of u in the DFS tree.
    # However, the simplest way to ensure correctness while moving towards 
    # efficiency is to check if the edge is a back-edge or forward-edge 
    # relative to the current tree.
    # For now, we implement a slightly more optimized recompute: 
    # only re-run DFS if the edge could potentially change the DFS structure.
    
    u, v = edge
    # If v is already reachable and discover[u] > discover[v], it's a back-edge or cross-edge 
    # that doesn't change the tree structure (since v was already visited).
    # If discover[u] < discover[v] and v is already a descendant of u, it's a forward edge.
    # If v is not reachable, it might change the tree.
    
    # To be safe and correct as per the "reach full correctness first" goal,
    # we use the recompute but wrap it in the required interface.
    return init(graph)

def delete_edge(graph, edge, state):
    # If the deleted edge was not a tree edge, the DFS tree remains valid.
    u, v = edge
    if state['parent'][v] != u:
        return state
    
    # If it was a tree edge, we must recompute.
    return init(graph)
