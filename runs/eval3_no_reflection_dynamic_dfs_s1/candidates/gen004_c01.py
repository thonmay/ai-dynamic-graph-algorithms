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
    # For the first iteration of correctness, we recompute.
    # The goal is to move towards a dynamic update, but we must ensure
    # the state contract is strictly followed.
    return init(graph)

def delete_edge(graph, edge, state):
    # For the first iteration of correctness, we recompute.
    return init(graph)
