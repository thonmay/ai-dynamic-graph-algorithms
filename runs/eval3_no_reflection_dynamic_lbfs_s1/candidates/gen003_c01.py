def lex_bfs(graph):
    n = len(graph)
    if n == 0:
        return []
    
    # Partition refinement implementation of LexBFS
    # Initial partition contains all vertices
    partitions = [list(range(n))]
    ordering = []
    
    while partitions:
        # Pick the first vertex from the first partition
        u = partitions[0].pop(0)
        if not partitions[0]:
            partitions.pop(0)
        
        ordering.append(u)
        
        # Refine partitions based on adjacency to u
        new_partitions = []
        for p in partitions:
            adj_u = []
            non_adj_u = []
            for v in p:
                if graph[u][v]:
                    adj_u.append(v)
                else:
                    non_adj_u.append(v)
            
            if adj_u:
                new_partitions.append(adj_u)
            if non_adj_u:
                new_partitions.append(non_adj_u)
        
        partitions = new_partitions
        
    return ordering

def init(graph):
    state = {}
    state['ordering'] = lex_bfs(graph)
    return state

def insert_edge(graph, edge, state):
    # Recompute to ensure correctness as per the goal of reaching full correctness first.
    # LexBFS is sensitive to edge changes; a full recompute is the safest baseline.
    state['ordering'] = lex_bfs(graph)
    return state

def delete_edge(graph, edge, state):
    # Recompute to ensure correctness.
    state['ordering'] = lex_bfs(graph)
    return state
