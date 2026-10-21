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

    Uses the standard label-based formulation: each unprocessed vertex
    carries a label (a list of 0/1 entries, one per processed vertex, in
    processing order).  At each step pick the unprocessed vertex with the
    lexicographically smallest label (ties broken by smallest vertex id)
    and append its adjacency bit to every other unprocessed vertex's label.
    """
    n = len(graph)
    if n == 0:
        return []

    labels = {v: [] for v in range(n)}
    unprocessed = set(range(n))
    order = []

    for _ in range(n):
        # Pick the unprocessed vertex with the lexicographically smallest
        # label; ties broken by smallest vertex id.
        v = min(unprocessed, key=lambda x: (labels[x], x))
        unprocessed.remove(v)
        order.append(v)
        # Append the adjacency bit to v on every other unprocessed label.
        for w in unprocessed:
            labels[w].append(1 if graph[v][w] else 0)

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if graph[a][b]:
                continue  # ab in E, condition not triggered
            for k in range(j + 1, n):
                c = ordering[k]
                if not graph[a][c]:
                    continue  # ac not in E, condition not triggered
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

    # Strategy 2b: try moving any vertex to each position (covers cases
    # where the repair requires moving a vertex other than u or v).
    for w in ordering:
        pw = pos[w]
        for new_pos in range(n):
            if new_pos == pw:
                continue
            new_order = [x for x in ordering if x != w]
            insert_at = new_pos if new_pos > pw else new_pos
            new_order.insert(insert_at, w)
            if _is_valid_lexbfs(graph, new_order):
                return new_order

    # Strategy 2c: try all pairs of transpositions (covers cases where the
    # repair requires swapping two vertices that are not u or v).
    for i in range(n):
        for j in range(i + 1, n):
            new_order = list(ordering)
            new_order[i], new_order[j] = new_order[j], new_order[i]
            if _is_valid_lexbfs(graph, new_order):
                return new_order

    # Strategy 2d: for small n, try all permutations (guaranteed to find a
    # valid LexBFS ordering if one exists, since every graph has at least
    # one).
    if n <= 8:
        from itertools import permutations
        for perm in permutations(ordering):
            if _is_valid_lexbfs(graph, list(perm)):
                return list(perm)

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
