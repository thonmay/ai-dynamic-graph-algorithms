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
    
    # A new edge (u, v) only changes the DFS tree if u is reachable from root
    # and v is not currently a descendant of u in the DFS tree.
    # If v is already discovered and discover[u] < discover[v] < finish[v] < finish[u],
    # then v is already a descendant of u.
    # However, the simplest way to ensure correctness for this calibration 
    # is to check if the edge (u, v) creates a "forward-cross" edge.
    # In a DFS tree, an edge (u, v) is a cross edge if discover[v] < discover[u] 
    # and v is not an ancestor of u.
    # A forward edge is if discover[u] < discover[v] and v is a descendant.
    
    # To avoid full recompute every time, we can check if the edge is "redundant".
    # But for the first step towards optimization, let's implement a slightly 
    # smarter recompute or just stick to the contract.
    # Given the goal "Reach full correctness first, then avoid a full recompute",
    # and the parent already does full recompute, I will implement a version 
    # that only recomputes if the edge could actually change the DFS structure.
    
    # If u is not reachable, the edge (u, v) cannot be part of the DFS tree from root 0.
    if state['discover'][u] == -1:
        return state
    
    # If v is already a descendant of u, the DFS tree doesn't change.
    if state['discover'][v] != -1 and state['discover'][u] < state['discover'][v] and state['finish'][v] < state['finish'][u]:
        return state

    # Otherwise, the edge might change the DFS tree.
    return init(graph)

def delete_edge(graph, edge, state):
    u, v = edge
    # If (u, v) was not a tree edge, deleting it doesn't change the DFS tree.
    if state['parent'][v] != u:
        return state
    
    # If it was a tree edge, we must recompute.
    return init(graph)
