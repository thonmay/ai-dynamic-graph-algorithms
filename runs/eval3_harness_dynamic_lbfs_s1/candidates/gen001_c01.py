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
            # Split p into p_neighbors and p_non_neighbors of u
            p_neighbors = {v for v in p if graph[u][v]}
            p_non_neighbors = p - p_neighbors
            
            if p_neighbors:
                new_partitions.append(p_neighbors)
            if p_non_neighbors:
                new_partitions.append(p_non_neighbors)
        
        # This simple split isn't correct for LexBFS.
        # LexBFS requires that if we split p into (p_neighbors, p_non_neighbors),
        # p_neighbors must come BEFORE p_non_neighbors, and this must be done
        # for all existing partitions in order.
        # Wait, the simple loop above does exactly that: it processes partitions
        # in order and puts neighbors before non-neighbors.
        # Let's re-verify the partition refinement logic.
        # In LexBFS, the current vertex u's neighbors in each partition are moved
        # to a new partition that precedes the non-neighbors of u in that same partition.
        
        partitions = new_partitions
        
    return ordering

def init(graph):
    return {'ordering': lex_bfs(graph)}

def insert_edge(graph, edge, state):
    return {'ordering': lex_bfs(graph)}

def delete_edge(graph, edge, state):
    return {'ordering': lex_bfs(graph)}
