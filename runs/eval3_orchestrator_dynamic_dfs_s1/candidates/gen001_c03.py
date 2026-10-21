def init(graph):
    n = len(graph)
    state = {
        'parent': [None] * n,
        'discover': [-1] * n,
        'finish': [-1] * n,
        'time': 0
    }
    
    def dfs(u, p):
        state['time'] += 1
        state['discover'][u] = state['time']
        state['parent'][u] = p
        for v in range(n):
            if graph[u][v] and state['discover'][v] == -1:
                dfs(v, u)
        state['time'] += 1
        state['finish'][u] = state['time']

    dfs(0, None)
    return state

def insert_edge(graph, edge, state):
    # For the first version, we recompute from scratch to ensure correctness.
    # The goal is to reach full correctness first.
    return init(graph)

def delete_edge(graph, edge, state):
    # For the first version, we recompute from scratch to ensure correctness.
    return init(graph)
