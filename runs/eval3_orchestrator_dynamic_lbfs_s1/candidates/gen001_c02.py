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
        # The neighbors of u are "more preferred" than non-neighbors.
        # However, the partition refinement must maintain the relative order 
        # of existing partitions.
        # The standard algorithm: for each partition P_i, split it into P_i_adj and P_i_nonadj.
        # The new sequence of partitions is P_0_adj, P_0_nonadj, P_1_adj, P_1_nonadj...
        # Wait, the standard LexBFS refinement is: 
        # For each partition P in the current list, split P into P_adj and P_nonadj.
        # Replace P with P_adj followed by P_nonadj.
        
        # Let's re-implement the refinement correctly.
        # The loop above already does this by iterating through partitions and appending adj then nonadj.
        # But wait, the order should be: for each partition, the neighbors come first.
        # Let's refine the loop.
        
    # The logic above is slightly flawed because it modifies partitions while iterating.
    # Let's rewrite the static LexBFS clearly.
    return {'ordering': _static_lexbfs(graph)}

def _static_lexbfs(graph):
    n = len(graph)
    if n == 0: return []
    
    ordering = []
    # partitions is a list of sets
    partitions = [set(range(n))]
    
    while len(ordering) < n:
        # 1. Pick vertex u from the first partition
        u = next(iter(partitions[0]))
        ordering.append(u)
        
        # 2. Remove u from its partition
        partitions[0].remove(u)
        if not partitions[0]:
            partitions.pop(0)
            
        # 3. Refine
        new_partitions = []
        for s in partitions:
            s_adj = {v for v in s if graph[u][v]}
            s_nonadj = s - s_adj
            if s_adj:
                new_partitions.append(s_adj)
            if s_nonadj:
                new_partitions.append(s_nonadj)
        partitions = new_partitions
        
    return ordering

def insert_edge(graph, edge, state):
    """
    Inserts an edge and updates the LexBFS ordering.
    For now, we recompute to ensure correctness.
    """
    return {'ordering': _static_lexbfs(graph)}

def delete_edge(graph, edge, state):
    """
    Deletes an edge and updates the LexBFS ordering.
    For now, we recompute to ensure correctness.
    """
    return {'ordering': _static_lexbfs(graph)}
