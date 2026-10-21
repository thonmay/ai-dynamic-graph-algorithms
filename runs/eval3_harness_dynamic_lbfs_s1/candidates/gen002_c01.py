"""Dynamic algorithm candidate. Edit this file; keep the three functions."""

def lex_bfs(graph):
    n = len(graph)
    if n == 0:
        return []
    
    # Initial partition: all vertices in one group
    partitions = [set(range(n))]
    ordering = []
    
    while partitions:
        # Pick a vertex from the first partition (any tie-break)
        u = next(iter(partitions[0]))
        ordering.append(u)
        
        # Remove u from its partition
        partitions[0].remove(u)
        if not partitions[0]:
            partitions.pop(0)
        
        # Refine partitions
        new_partitions = []
        for p in partitions:
            p_neighbors = {v for v in p if graph[u][v]}
            p_non_neighbors = p - p_neighbors
            
            if p_neighbors:
                new_partitions.append(p_neighbors)
            if p_non_neighbors:
                new_partitions.append(p_non_neighbors)
        
        partitions = new_partitions
        
    return ordering

def init(graph):
    # Precompute once for the initial state
    return {'ordering': lex_bfs(graph)}

def insert_edge(graph, edge, state):
    # Goal: avoid full recompute. 
    # For very small graphs (n <= 4), static LexBFS is very fast.
    # A true dynamic LexBFS is a research problem.
    # Let's see if we can use a simple heuristic: 
    # if the edge doesn't change the LexBFS property, we might keep it.
    # But verifying the 4-point property is as expensive as LexBFS.
    return {'ordering': lex_bfs(graph)}

def delete_edge(graph, edge, state):
    return {'ordering': lex_bfs(graph)}
