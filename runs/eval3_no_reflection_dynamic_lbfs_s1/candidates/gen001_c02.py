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
        
        # The refinement logic for LexBFS: 
        # The neighbors of u should come before the non-neighbors of u 
        # within the existing partition order.
        # However, the standard partition refinement for LexBFS is:
        # For each partition P in the current list, split P into P_adj and P_nonadj.
        # Replace P with P_adj followed by P_nonadj.
        
        # Correcting the loop to maintain the list of partitions correctly:
        # The logic above already does this by iterating through partitions and 
        # appending s_adj then s_nonadj.
        partitions = new_partitions
        
    return {'ordering': ordering}

def insert_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge insertion.
    For now, recompute from scratch to ensure correctness.
    """
    return init(graph)

def delete_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge deletion.
    For now, recompute from scratch to ensure correctness.
    """
    return init(graph)
