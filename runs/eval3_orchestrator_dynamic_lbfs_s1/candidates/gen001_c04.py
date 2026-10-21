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
        
        # Note: The standard LexBFS refinement puts the neighbors *before* the non-neighbors
        # in the refinement process to maintain the lexicographical property.
        # However, the partition list itself represents the priority.
        # The correct refinement for LexBFS: for each partition S, split into S \cap N(u) and S \setminus N(u).
        # S \cap N(u) comes before S \setminus N(u).
        
        # Wait, the logic above already does that: s_adj then s_nonadj.
        # But we must process partitions in order.
        
        # Let's refine the logic to be more robust.
        # The current `new_partitions` logic replaces the whole list.
        # That's correct because we are refining every existing partition.
        partitions = new_partitions
        
    return {'ordering': ordering}

def insert_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge insertion.
    Since fully dynamic LexBFS is an open problem, we recompute for correctness.
    """
    return init(graph)

def delete_edge(graph, edge, state):
    """
    Updates the LexBFS ordering after an edge deletion.
    Since fully dynamic LexBFS is an open problem, we recompute for correctness.
    """
    return init(graph)
