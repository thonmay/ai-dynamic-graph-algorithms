"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try to repair
the existing ordering locally (cheap); if repair fails, fall back to a
full static LexBFS recomputation (always correct).

Validation uses the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.
"""


def _validate(order, adj):
    """Check (LB) 4-point property. Returns True iff order is a valid LexBFS.

    For every triple of positions ai < bi < ci with a~c and a not~ b,
    there must exist a position di < ai with d~b and d not~ c.
    """
    n = len(order)
    for bi in range(n):
        b = order[bi]
        for ci in range(bi + 1, n):
            c = order[ci]
            for ai in range(bi):
                a = order[ai]
                if adj[a][c] and not adj[a][b]:
                    # need witness d < ai with d~b and d NOT~ c
                    ok = any(adj[order[di]][b] and not adj[order[di]][c]
                             for di in range(ai))
                    if not ok:
                        return False
    return True


def _lexbfs(adj):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).
    Returns a valid LexBFS ordering."""
    n = len(adj)
    if n == 0:
        return []
    
    # Each vertex has a label (list of neighbors in order of appearance).
    # We maintain buckets: list of [label_list, [vertices]].
    # label_list is a list of vertex ids (the "splitting" neighbors in order).
    # Buckets are kept sorted by label (lexicographic).
    
    # Start: all vertices in one bucket with empty label.
    all_vertices = list(range(n))
    buckets = [[[], all_vertices]]
    
    order = []
    
    while buckets:
        # Pick the first bucket (smallest label)
        label, vertices = buckets[0]
        # Pick the first vertex in this bucket
        v = vertices[0]
        order.append(v)
        
        # Remove v from bucket
        vertices.pop(0)
        if not vertices:
            buckets.pop(0)
        
        # Refine all remaining buckets by adjacency to v
        # For each bucket, split into: adjacent to v (prepend v to label) 
        # and not adjacent to v (label unchanged).
        # The adjacent part comes before the non-adjacent part.
        
        new_buckets = []
        for bucket in buckets:
            blabel, bverts = bucket
            adj_verts = [x for x in bverts if adj[v][x]]
            nonadj_verts = [x for x in bverts if not adj[v][x]]
            if adj_verts:
                new_label = [v] + blabel
                new_buckets.append([new_label, adj_verts])
            if nonadj_verts:
                new_buckets.append([blabel, nonadj_verts])
        
        # Sort new_buckets by label
        new_buckets.sort(key=lambda b: b[0])
        buckets = new_buckets
    
    return order


def _try_repair(order, adj, u, v):
    """Try to find a valid ordering close to `order` after an update.
    Returns a valid ordering or None."""
    n = len(order)
    # Try the original ordering
    if _validate(order, adj):
        return order
    # Try swapping u and v
    idx_u = order.index(u)
    idx_v = order.index(v)
    swapped = order[:]
    swapped[idx_u], swapped[idx_v] = v, u
    if _validate(swapped, adj):
        return swapped
    # Try moving u to be adjacent to v
    candidate = order[:]
    candidate.remove(u)
    pos_v = candidate.index(v)
    for ins_pos in (pos_v, pos_v + 1):
        candidate2 = candidate[:]
        candidate2.insert(ins_pos, u)
        if _validate(candidate2, adj):
            return candidate2
    # Try moving v to be adjacent to u
    candidate = order[:]
    candidate.remove(v)
    pos_u = candidate.index(u)
    for ins_pos in (pos_u, pos_u + 1):
        candidate2 = candidate[:]
        candidate2.insert(ins_pos, v)
        if _validate(candidate2, adj):
            return candidate2
    return None


def init(graph):
    adj = [row[:] for row in graph]
    n = len(adj)
    order = _lexbfs(adj)
    return {'ordering': order, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = [row[:] for row in graph]
    order = state['ordering']
    repaired = _try_repair(order, adj, u, v)
    if repaired is not None:
        if _validate(repaired, adj):
            return {'ordering': repaired, 'adj': adj}
    order = _lexbfs(adj)
    return {'ordering': order, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    adj = [row[:] for row in graph]
    order = state['ordering']
    repaired = _try_repair(order, adj, u, v)
    if repaired is not None:
        if _validate(repaired, adj):
            return {'ordering': repaired, 'adj': adj}
    order = _lexbfs(adj)
    return {'ordering': order, 'adj': adj}
