"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder a small window of the ordering to restore the
(LB) 4-point property). If the local repair fails, fall back to a full
recomputation of a LexBFS ordering from scratch.

The (LB) 4-point property (Corneil & Krueger): for all positions
a < b < c with ac in E and ab not in E, there exists d < a with
db in E and dc not in E.
"""


def _lexbfs_ordering(adj, n):
    """Compute a valid LexBFS ordering using partition refinement.

    adj: list of lists, 0/1 adjacency matrix.
    Returns a list of n vertices in LexBFS order.
    """
    if n == 0:
        return []

    output = []
    remaining = list(range(n))
    # label[v] = tuple of 0/1, one per output vertex
    labels = {v: () for v in range(n)}

    while remaining:
        # Find the vertex with the lexicographically smallest label
        # among remaining vertices.
        best = None
        best_label = None
        for v in remaining:
            if best is None or labels[v] < best_label or (labels[v] == best_label and v < best):
                best = v
                best_label = labels[v]

        output.append(best)
        remaining.remove(best)

        # Update labels of remaining vertices
        for v in remaining:
            bit = adj[best][v]
            labels[v] = labels[v] + (bit,)

    return output


def _check_lb_property(ordering, adj, n):
    """Check the (LB) 4-point property.

    For all positions a < b < c (positions in the ordering) with
    ac in E and ab not in E, there exists d < a with
    db in E and dc not in E.

    Returns True if valid, False otherwise.
    """
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if adj[va][vb]:
                continue  # ab in E, no constraint
            # ab not in E. For all c > b with ac in E, need certifier.
            for c in range(b + 1, n):
                vc = ordering[c]
                if not adj[va][vc]:
                    continue  # ac not in E, no constraint
                # Need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if adj[vd][vb] and not adj[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_local_repair(ordering, adj, n, edge):
    """Try to fix the ordering locally after an edge update.

    Returns a new ordering if successful, None if local repair fails.
    """
    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    candidates = []

    # Swap u and v
    if pos[u] != pos[v]:
        new_order = ordering[:]
        new_order[pos[u]], new_order[pos[v]] = new_order[pos[v]], new_order[pos[u]]
        candidates.append(new_order)

    # Move u to various positions near v
    for delta in range(-3, 4):
        target = pos[v] + delta
        if 0 <= target < n and target != pos[u]:
            new_order = ordering[:]
            new_order.pop(pos[u])
            if target > pos[u]:
                target -= 1
            if 0 <= target < n:
                new_order.insert(target, u)
                candidates.append(new_order)

    # Move v to various positions near u
    for delta in range(-3, 4):
        target = pos[u] + delta
        if 0 <= target < n and target != pos[v]:
            new_order = ordering[:]
            new_order.pop(pos[v])
            if target > pos[v]:
                target -= 1
            if 0 <= target < n:
                new_order.insert(target, v)
                candidates.append(new_order)

    # Try all single-vertex moves for u and v to any position
    for x in (u, v):
        for target in range(n):
            if target == pos[x]:
                continue
            new_order = ordering[:]
            new_order.pop(pos[x])
            if target > pos[x]:
                target -= 1
            if 0 <= target < n:
                new_order.insert(target, x)
                candidates.append(new_order)

    # Check each candidate
    for cand in candidates:
        if _check_lb_property(cand, adj, n):
            return cand

    return None


def init(graph):
    n = len(graph)
    ordering = _lexbfs_ordering(graph, n)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    ordering = state['ordering']

    # Try local repair first
    repaired = _try_local_repair(ordering, graph, n, edge)
    if repaired is not None:
        return {'ordering': repaired, 'n': n}

    # Fallback: full recompute
    ordering = _lexbfs_ordering(graph, n)
    return {'ordering': ordering, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    ordering = state['ordering']

    # Try local repair first
    repaired = _try_local_repair(ordering, graph, n, edge)
    if repaired is not None:
        return {'ordering': repaired, 'n': n}

    # Fallback: full recompute
    ordering = _lexbfs_ordering(graph, n)
    return {'ordering': ordering, 'n': n}
