def init(graph):
    n = len(graph)
    root = 0
    distances = [-1] * n
    parent = [None] * n
    
    distances[root] = 0
    queue = [root]
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v in range(n):
            if graph[u][v] == 1 and distances[v] == -1:
                distances[v] = distances[u] + 1
                parent[v] = u
                queue.append(v)
                
    return {'distances': distances, 'parent': parent}

def insert_edge(graph, edge, state):
    # For now, perform full recomputation to ensure correctness.
    # This will be optimized in later generations.
    return init(graph)

def delete_edge(graph, edge, state):
    # For now, perform full recomputation to ensure correctness.
    return init(graph)
