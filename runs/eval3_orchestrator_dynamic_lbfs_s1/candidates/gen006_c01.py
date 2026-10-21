def init(graph):
    """
    Initializes the LexBFS ordering for the given graph using partition refinement.
    """
    n = len(graph)
    if n == 0:
        return {'ordering': []}
    
    ordering = []
    # Initial partition: one set containing all vertices
    partitions = [set(range(n))]
    
    while len(ordering) < n:
        # Pick a vertex from the first partition
        # To ensure consistency, we could pick the min vertex, but any is valid.
        u = min(partitions[0])
        ordering.append(u)
        
        # Remove u from its partition
        partitions[0].remove(u)
        if not partitions[0]:
            partitions.pop(0)
            
        # Refine partitions based on adjacency to u
        new_partitions = []
        for s in partitions:
            # Split s into s_adj (neighbors of u) and s_nonadj (non-neighbors of u)
            s_adj = {v for v in s if graph[u][v]}
            s_nonadj = s - s_adj
            
            # LexBFS refinement: neighbors of the chosen vertex are placed 
            # in a higher priority partition than non-neighbors.
            if s_adj:
                new_partitions.append(s_adj)
            if s_nonadj:
                new_partitions.append(s_nonadj)
        
        partitions = new_partitions
        
    return {'ordering': ordering}

def insert_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge insertion.
    Recomputes from scratch to ensure correctness.
    """
    return init(graph)

def delete_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge deletion.
    Recomputes from scratch to ensure correctness.
    """
    return init(graph)
