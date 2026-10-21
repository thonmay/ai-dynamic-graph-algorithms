def init(graph):
    n = len(graph)
    state = {
        'parent': [None] * n,
        'discover': [-1] * n,
        'finish': [-1] * n,
    }
    
    timer = [0]
    visited = [False] * n

    def dfs(u, p):
        visited[u] = True
        timer[0] += 1
        state['discover'][u] = timer[0]
        state['parent'][u] = p
        for v in range(n):
            if graph[u][v] and not visited[v]:
                dfs(v, u)
        timer[0] += 1
        state['finish'][u] = timer[0]

    dfs(0, None)
    return state

def insert_edge(graph, edge, state):
    # To ensure correctness and meet the goal of avoiding full recompute,
    # we check if the new edge (u, v) creates a forward-cross edge.
    # A forward-cross edge is an edge u -> v where discover[u] < discover[v]
    # but v is not a descendant of u.
    # However, for this calibration step, we will implement a slightly
    # more robust re-computation that only triggers if the edge could
    # potentially change the DFS structure.
    
    u, v = edge
    n = len(graph)
    
    # If v is already reachable and the edge doesn't violate DFS properties,
    # we might not need to recompute. But the safest way to maintain 
    # a valid DFS tree is to re-run DFS if the edge is "critical".
    # For now, to ensure 100% correctness while moving away from 
    # blind re-init, we check if v was previously unreachable or 
    # if u is discovered after v.
    
    if state['discover'][v] == -1 or state['discover'][u] > state['discover'][v]:
        # This edge might create a new path or change the discovery order.
        return init(graph)
    
    # Check if v is a descendant of u.
    # v is a descendant of u iff discover[u] < discover[v] < finish[v] < finish[u].
    if not (state['discover'][u] < state['discover'][v] < state['finish'][v] < state['finish'][u]):
        # This is a cross-edge (u discovered before v, but v not descendant).
        # In a DFS tree, cross-edges are allowed if they go to a vertex 
        # discovered and finished before the current vertex.
        # But if discover[u] < discover[v], it must be a tree/forward edge.
        # Since it's not a descendant, it's a forward-cross edge, which is forbidden.
        return init(graph)

    return state

def delete_edge(graph, edge, state):
    u, v = edge
    # If the deleted edge was not a tree edge, the DFS structure remains valid.
    if state['parent'][v] != u:
        return state
    
    # If it was a tree edge, we must recompute.
    return init(graph)
