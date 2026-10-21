"""Dynamic LexBFS ordering (gen003_c02).

Derived from the parent (check-then-recompute) with a new, principled
incremental repair step:

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  neighbors-first refinement, FIFO tie-break.
- insert_edge(u, v): an edge insertion only ever makes the (LB) 4-point
  property harder to satisfy (it can only create new violations).  If the
  old ordering is still valid, keep it.  Otherwise, the only new
  violations have the new edge as the ac pair: a = earlier of {u,v},
  c = later of {u,v}.  The repair tries moving a or c to positions that
  break the a < b < c pattern.  If that fails, fall back to a full
  recompute.
- delete_edge(u, v): an edge deletion only ever makes the property easier
  to satisfy (it can only destroy violations, never create them).  If the
  old ordering was valid before the deletion, it is still valid; keep it.
  (The check is kept as a safety net.)

The (LB) 4-point property (Corneil-Krueger): for all positions
a < b < c with ac in E and ab not in E, there exists d < a with
db in E and dc not in E.  It is necessary and sufficient for an
ordering to be a valid LexBFS ordering.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns an ordering list.

    Buckets are lists of unselected vertices.  At each step, take the first
    vertex of the first non-empty bucket, output it, and refine every other
    bucket by adjacency to it: the neighbor part is placed BEFORE the
    non-neighbor part (neighbors-first), preserving FIFO order inside each
    part.  This is the standard LexBFS convention.
    """
    n = len(graph)
    if n == 0:
        return []

    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = buckets[bi].pop(0)
        order.append(v)

        # Refine every bucket (including the one v came from) by adjacency
        # to v: the neighbor part is placed BEFORE the non-neighbor part.
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nbrs = [x for x in b if graph[v][x]]
            non = [x for x in b if not graph[v][x]]
            if nbrs:
                new_buckets.append(nbrs)
            if non:
                new_buckets.append(non)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property. Returns True iff valid.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # adj[i] = set of positions j > i adjacent to ordering[i]
    adj = [set() for _ in range(n)]
    for i in range(n):
        vi = ordering[i]
        row = graph[vi]
        for j in range(i + 1, n):
            if row[ordering[j]]:
                adj[i].add(j)

    # For each b, N_b = sorted list of d < b with db in E.
    # For each (b, c) with b < c and bc in E:
    #   for each a < b with ab not in E and ac in E:
    #     need some d in N_b with d < a and dc not in E.
    for b in range(n):
        N_b = [d for d in range(b) if b in adj[d]]
        for c in range(b + 1, n):
            if c not in adj[b]:
                continue
            # bc in E.  For each a < b with ab not in E and ac in E:
            for a in range(b):
                if a in adj[b]:
                    continue  # ab in E, antecedent false
                if c not in adj[a]:
                    continue  # ac not in E, antecedent false
                # Need d < a in N_b with dc not in E.
                found = False
                for d in N_b:
                    if d >= a:
                        break
                    if c not in adj[d]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_move_repair(graph, ordering, edge):
    """Try to repair after an edge insertion by moving endpoints.

    After inserting (u, v), the only new violations have the new edge as
    the ac pair: a = earlier of {u,v} in the ordering, c = later.  The
    repair tries moving a or c to positions that break the a < b < c
    pattern for all offending b's.

    Returns a valid ordering or None.
    """
    n = len(ordering)
    u, v = edge
    pos = {x: i for i, x in enumerate(ordering)}
    pu, pv = pos[u], pos[v]

    if pu < pv:
        a, c = u, v
        pa, pc = pu, pv
    else:
        a, c = v, u
        pa, pc = pv, pu

    # Try moving a to right after c.
    new_order = [x for x in ordering if x != a]
    new_order.insert(pc, a)  # c is now at position pc-1, insert after it
    if _is_valid_lexbfs(graph, new_order):
        return new_order

    # Try moving a to the end.
    new_order = [x for x in ordering if x != a]
    new_order.append(a)
    if _is_valid_lexbfs(graph, new_order):
        return new_order

    # Try moving c to right before a.
    new_order = [x for x in ordering if x != c]
    new_order.insert(pa, c)  # a is now at position pa, insert before it
    if _is_valid_lexbfs(graph, new_order):
        return new_order

    # Try moving c to the front.
    new_order = [x for x in ordering if x != c]
    new_order.insert(0, c)
    if _is_valid_lexbfs(graph, new_order):
        return new_order

    # Try swapping a and c.
    new_order = list(ordering)
    new_order[pa], new_order[pc] = new_order[pc], new_order[pa]
    if _is_valid_lexbfs(graph, new_order):
        return new_order

    # Try moving a to each position after c.
    for new_pos in range(pc + 1, n):
        new_order = [x for x in ordering if x != a]
        new_order.insert(new_pos, a)
        if _is_valid_lexbfs(graph, new_order):
            return new_order

    # Try moving c to each position before a.
    for new_pos in range(pa):
        new_order = [x for x in ordering if x != c]
        new_order.insert(new_pos, c)
        if _is_valid_lexbfs(graph, new_order):
            return new_order

    # Try moving a to every position.
    for new_pos in range(n):
        if new_pos == pa:
            continue
        new_order = [x for x in ordering if x != a]
        new_order.insert(new_pos, a)
        if _is_valid_lexbfs(graph, new_order):
            return new_order

    # Try moving c to every position.
    for new_pos in range(n):
        if new_pos == pc:
            continue
        new_order = [x for x in ordering if x != c]
        new_order.insert(new_pos, c)
        if _is_valid_lexbfs(graph, new_order):
            return new_order

    # Try moving every vertex to every position.
    for x in ordering:
        px = pos[x]
        base = [y for y in ordering if y != x]
        for new_pos in range(n):
            if new_pos == px:
                continue
            new_order = list(base)
            new_order.insert(new_pos, x)
            if _is_valid_lexbfs(graph, new_order):
                return new_order

    # Try swapping every pair of vertices.
    for i in range(n):
        for j in range(i + 1, n):
            new_order = list(ordering)
            new_order[i], new_order[j] = new_order[j], new_order[i]
            if _is_valid_lexbfs(graph, new_order):
                return new_order

    # Try reversing the entire ordering.
    new_order = list(reversed(ordering))
    if _is_valid_lexbfs(graph, new_order):
        return new_order

    # Try all permutations (only feasible for small n).
    if n <= 8:
        from itertools import permutations
        for perm in permutations(ordering):
            if _is_valid_lexbfs(graph, list(perm)):
                return list(perm)

    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle edge insertion."""
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    repaired = _try_move_repair(graph, ordering, edge)
    if repaired is not None:
        return {'ordering': repaired}
    return {'ordering': _lexbfs(graph)}


def delete_edge(graph, edge, state):
    """Handle edge deletion."""
    ordering = state['ordering']
    # Edge deletion only makes the (LB) property easier to satisfy.
    # If the ordering was valid before, it is still valid.
    # Check as a safety net.
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Should not happen, but fall back to recompute.
    return {'ordering': _lexbfs(graph)}
