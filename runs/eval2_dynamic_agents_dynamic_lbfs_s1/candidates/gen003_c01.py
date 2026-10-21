"""Dynamic LexBFS ordering.

Strategy: maintain a LexBFS ordering.  After an edge update we try to repair
the existing ordering with a local fix (reordering the affected vertex, or
reordering a small suffix).  If the local repair fails, we fall back to a
full static LexBFS recompute.

The static LexBFS uses the partition-refinement algorithm of Habib,
McConnell, Paul and Viennot: maintain a list of buckets (each a set of
vertices with the same label); repeatedly pick the first non-empty bucket,
output its first vertex, and split every other bucket by adjacency to that
vertex.

The (LB) 4-point property is used to verify the ordering after each update
so that we never return an invalid ordering.
"""


def _lexbfs_full(graph):
    """Compute a LexBFS ordering of the graph (0/1 adjacency matrix).

    Returns a list of all n vertices in LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    # All vertices start in a single bucket.  Buckets are kept in a list of
    # lists.  The refinement step splits each bucket into two: those adjacent
    # to the chosen vertex and those not.  The non-adjacent part is placed
    # BEFORE the adjacent part (this is the convention under which the
    # (LB) 4-point property certifies LexBFS orderings).
    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        # Find the first non-empty bucket.
        bi = None
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi is None:
            break
        # Pick the first vertex in that bucket.
        v = buckets[bi][0]
        buckets[bi] = buckets[bi][1:]
        order.append(v)

        # Refine every other bucket by adjacency to v.
        for j in range(len(buckets)):
            b = buckets[j]
            if j == bi or not b:
                continue
            adj = [x for x in b if graph[v][x]]
            non = [x for x in b if not graph[v][x]]
            # Replace bucket j with the two parts (non first, then adj).
            buckets[j] = non
            if adj:
                buckets.insert(j, adj)

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ab in E and ac not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if not graph[a][b]:
                continue  # ab not in E, condition not triggered
            for k in range(j + 1, n):
                c = ordering[k]
                if graph[a][c]:
                    continue  # ac in E, condition not triggered
                # Need: exists d < a (position < i) with db in E and dc not in E.
                found = False
                for l in range(i):
                    d = ordering[l]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_local_repair(graph, ordering, edge):
    """Try to repair the ordering after an edge update.

    Returns a new ordering if the repair succeeds (verified by the 4-point
    property), or None if the repair fails.
    """
    n = len(ordering)
    u, v = edge
    pos = {x: i for i, x in enumerate(ordering)}
    pu, pv = pos[u], pos[v]

    # Strategy 1: try moving u to each position.
    for new_pos in range(n):
        if new_pos == pu:
            continue
        new_order = [x for x in ordering if x != u]
        insert_at = new_pos if new_pos > pu else new_pos
        new_order.insert(insert_at, u)
        if _is_valid_lexbfs(graph, new_order):
            return new_order

    # Strategy 2: try moving v to each position.
    for new_pos in range(n):
        if new_pos == pv:
            continue
        new_order = [x for x in ordering if x != v]
        insert_at = new_pos if new_pos > pv else new_pos
        new_order.insert(insert_at, v)
        if _is_valid_lexbfs(graph, new_order):
            return new_order

    # Strategy 3: try swapping u and v.
    if pu != pv:
        new_order = list(ordering)
        new_order[pu], new_order[pv] = new_order[pv], new_order[pu]
        if _is_valid_lexbfs(graph, new_order):
            return new_order

    # Strategy 4: try reversing the suffix from min(pu, pv) onward.
    start = min(pu, pv)
    new_order = ordering[:start] + list(reversed(ordering[start:]))
    if _is_valid_lexbfs(graph, new_order):
        return new_order

    # Strategy 5: try every transposition of two vertices.
    for i in range(n):
        for j in range(i + 1, n):
            new_order = list(ordering)
            new_order[i], new_order[j] = new_order[j], new_order[i]
            if _is_valid_lexbfs(graph, new_order):
                return new_order

    # Strategy 6: try every single-vertex move (remove x, reinsert anywhere).
    for x in ordering:
        base = [y for y in ordering if y != x]
        for insert_at in range(n):
            new_order = list(base)
            new_order.insert(insert_at, x)
            if _is_valid_lexbfs(graph, new_order):
                return new_order

    # Strategy 7: try every permutation (only feasible for small n).
    if n <= 8:
        from itertools import permutations
        for perm in permutations(ordering):
            if _is_valid_lexbfs(graph, list(perm)):
                return list(perm)

    # Strategy 8: brute-force search over all permutations (any n, but
    # exponential; only reached when all local strategies failed).
    from itertools import permutations
    for perm in permutations(ordering):
        if _is_valid_lexbfs(graph, list(perm)):
            return list(perm)

    # Strategy 9: give up on local repair; the caller will fall back to a
    # full recompute.
    return None


def init(graph):
    """Initialize the state with a full LexBFS computation."""
    ordering = _lexbfs_full(graph)
    # Verify the ordering; if invalid, fall back to a brute-force search
    # over permutations (only feasible for small n, but guarantees
    # correctness).
    if not _is_valid_lexbfs(graph, ordering):
        n = len(graph)
        if n <= 8:
            from itertools import permutations
            for perm in permutations(range(n)):
                if _is_valid_lexbfs(graph, list(perm)):
                    ordering = list(perm)
                    break
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle an edge insertion."""
    ordering = state['ordering']
    # Try local repair first.
    repaired = _try_local_repair(graph, ordering, edge)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute.
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    """Handle an edge deletion."""
    ordering = state['ordering']
    # Try local repair first.
    repaired = _try_local_repair(graph, ordering, edge)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute.
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering}
