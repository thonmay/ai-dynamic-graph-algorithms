def init(graph):
    """
    Initializes the LexBFS ordering for the given graph.
    """
    n = len(graph)
    if n == 0:
        return {'ordering': []}
    
    # Static LexBFS using partition refinement
    ordering = []
    # Initial partition: one set containing all vertices
    partitions = [set(range(n))]
    
    while len(ordering) < n:
        # Pick a vertex from the first partition
        u = next(iter(partitions[0]))
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
            
            if s_adj:
                new_partitions.append(s_adj)
            if s_nonadj:
                new_partitions.append(s_nonadj)
        
        # The refinement rule for LexBFS: 
        # For each existing partition, the neighbors of u are moved to a new 
        # partition that precedes the non-neighbors.
        # However, the standard partition refinement for LexBFS is:
        # For each partition P in the current list, split P into P \cap N(u) and P \setminus N(u).
        # Replace P with (P \cap N(u), P \setminus N(u)) in the list.
        # The logic above does exactly that.
        partitions = new_partitions
        
    return {'ordering': ordering}

def insert_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge insertion.
    For now, we recompute to ensure correctness.
    """
    return init(graph)

def delete_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge deletion.
    For now, we recompute to ensure correctness.
    """
    return init(graph)
