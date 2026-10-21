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
    
    # If v is not reachable from root, it might become reachable.
    # If v is reachable, we check if (u, v) is a forward-cross edge.
    # A forward-cross edge is an edge (u, v) where discover[u] < discover[v]
    # but v is not a descendant of u.
    # v is a descendant of u iff discover[u] < discover[v] < finish[v] < finish[u].
    
    if state['discover'][v] == -1:
        # v was unreachable, now it might be reachable via u.
        # If u is reachable, the tree structure definitely changes.
        if state['discover'][u] != -1:
            return init(graph)
        else:
            # Both u and v are unreachable, no change to the DFS tree from root 0.
            return state
    
    # v is already reachable.
    if state['discover'][u] == -1:
        # u is unreachable, edge (u, v) cannot be part of a DFS tree from root 0.
        return state
        
    # Both u and v are reachable.
    # If discover[u] > discover[v], it's a back-edge or cross-edge (v visited first).
    # This does not change the DFS tree.
    if state['discover'][u] > state['discover'][v]:
        return state
        
    # If discover[u] < discover[v], it's either a forward-edge or a forward-cross edge.
    # Forward-edge: v is a descendant of u.
    if state['discover'][u] < state['discover'][v] < state['finish'][v] < state['finish'][u]:
        return state
        
    # It's a forward-cross edge. This violates the DFS property.
    return init(graph)

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was not a tree edge, the DFS tree remains valid.
    # A tree edge is one where parent[v] == u.
    if state['parent'][v] != u:
        return state
    
    # If it was a tree edge, we must recompute.
    return init(graph)
