"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder only the affected vertices); if the repair
cannot certify validity, fall back to a full O(n^2) LexBFS recompute.

The local repair uses the (LB) 4-point property of Corneil & Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

Key insight for the repair:
- Edge insertion (u,v): the fix is to move the later of u,v to be just
  before the earlier one. This is a local change that should fix most
  violations.
- Edge deletion (u,v): the fix is to move the earlier of u,v to be just
  after the later one.

The repair is validated by a full (LB) check; if it fails, we recompute.
"""


def _lexbfs(graph):
    """Static LexBFS via bucket-based partition refinement. O(n^2).
    
    Returns a valid LexBFS ordering (list of all n vertices).
    """
    n = len(graph)
    if n == 0:
        return []

    # Bucket-based LexBFS:
    # - Start with one bucket containing all vertices (in id order)
    # - Repeatedly:
    #   1. Pick the first vertex v from the first non-empty bucket
    #   2. Add v to result
    #   3. Split the remaining vertices in that bucket by adjacency to v:
    #      - neighbors of v go to a new bucket at the front
    #      - non-neighbors stay
    #   4. The neighbor sub-bucket is placed before the non-neighbor sub-bucket

    buckets = [list(range(n))]
    result = []

    while len(result) < n:
        # Find the first non-empty bucket
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break

        # Pick the first vertex from this bucket
        v = buckets[bi][0]
        buckets[bi] = buckets[bi][1:]
        result.append(v)

        # Split the remaining vertices in bucket bi by adjacency to v
        remaining = buckets[bi]
        if not remaining:
            continue

        nbrs = []
        non_nbrs = []
        for w in remaining:
            if graph[v][w]:
                nbrs.append(w)
            else:
                non_nbrs.append(w)

        # Rebuild buckets:
        # - buckets[0:bi] unchanged
        # - at position bi: nbrs (if non-empty)
        # - then non_nbrs (if non-empty)
        # - then buckets[bi+1:] unchanged
        new_buckets = buckets[:bi]
        if nbrs:
            new_buckets.append(nbrs)
        if non_nbrs:
            new_buckets.append(non_nbrs)
        new_buckets.extend(buckets[bi + 1:])
        buckets = new_buckets

    return result


def _check_lb(graph, ordering):
    """Check the (LB) 4-point property. Returns True if valid.
    
    For all positions a < b < c (by position in ordering) with
    ac in E and ab not in E, there exists d < a with db in E and dc not in E.
    
    Optimized: for each (a, b) pair with ab not in E, precompute the set
    of c's that need a witness, then check if any d < a works for all of them.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # For each a_pos, precompute:
    #   non_nbrs_after[a_pos] = set of b_pos > a_pos where ab not in E
    #   For each such b, the set of c_pos > b_pos where ac in E
    #   For each d_pos < a_pos, the set of c_pos where db in E and dc not in E

    # Simpler approach: for each (a_pos, b_pos) with ab not in E,
    # collect all c_pos > b_pos where ac in E.
    # Then check if there exists d_pos < a_pos such that for ALL such c,
    # db in E and dc not in E.

    for a_pos in range(n):
        a = ordering[a_pos]
        for b_pos in range(a_pos + 1, n):
            b = ordering[b_pos]
            if graph[a][b]:
                continue  # ab in E, skip

            # Collect all c_pos > b_pos where ac in E
            c_list = []
            for c_pos in range(b_pos + 1, n):
                c = ordering[c_pos]
                if graph[a][c]:
                    c_list.append(c_pos)

            if not c_list:
                continue  # no c to check

            # Check if there exists d_pos < a_pos such that for ALL c in c_list,
            # db in E and dc not in E
            found = False
            for d_pos in range(a_pos):
                d = ordering[d_pos]
                if not graph[d][b]:
                    continue  # db not in E, this d doesn't work
                # Check all c in c_list: dc not in E
                all_ok = True
                for c_pos in c_list:
                    c = ordering[c_pos]
                    if graph[d][c]:
                        all_ok = False
                        break
                if all_ok:
                    found = True
                    break
            if not found:
                return False
    return True


def _try_repair_insert(graph, ordering, u, v):
    """Try to repair after inserting edge (u, v).

    The fix: move the later of u, v to be just before the earlier one.
    Returns the new ordering, or None if the repair fails the (LB) check.
    """
    n = len(ordering)
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i

    pu, pv = pos[u], pos[v]
    if pu == pv:
        return ordering  # shouldn't happen

    # The later vertex should move before the earlier one.
    if pu < pv:
        later, earlier = v, u
        p_later, p_earlier = pv, pu
    else:
        later, earlier = u, v
        p_later, p_earlier = pu, pv

    # Move 'later' from p_later to p_earlier
    # New ordering: [0..p_earlier-1], later, [p_earlier..p_later-1], [p_later+1..]
    new_order = ordering[:p_earlier] + [later] + ordering[p_earlier:p_later] + ordering[p_later + 1:]

    # Validate
    if _check_lb(graph, new_order):
        return new_order
    return None


def _try_repair_delete(graph, ordering, u, v):
    """Try to repair after deleting edge (u, v).

    The fix: move the earlier of u, v to be just after the later one.
    Returns the new ordering, or None if the repair fails the (LB) check.
    """
    n = len(ordering)
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i

    pu, pv = pos[u], pos[v]
    if pu == pv:
        return ordering

    # The earlier vertex should move after the later one.
    if pu < pv:
        earlier, later = u, v
        p_earlier, p_later = pu, pv
    else:
        earlier, later = u, v
        p_earlier, p_later = pu, pv

    # Move 'earlier' from p_earlier to p_later + 1
    # New ordering: [0..p_earlier-1], [p_earlier+1..p_later], earlier, [p_later+1..]
    new_order = (ordering[:p_earlier] + ordering[p_earlier + 1:p_later + 1]
                 + [earlier] + ordering[p_later + 1:])
    if len(new_order) != n:
        return None  # safety check

    # Validate
    if _check_lb(graph, new_order):
        return new_order
    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    """Handle edge insertion. Try local repair, fall back to recompute."""
    u, v = edge
    ordering = state['ordering']

    # Try local repair
    new_order = _try_repair_insert(graph, ordering, u, v)
    if new_order is not None:
        return {'ordering': new_order, 'n': state['n']}

    # Fallback: full recompute
    new_order = _lexbfs(graph)
    return {'ordering': new_order, 'n': state['n']}


def delete_edge(graph, edge, state):
    """Handle edge deletion. Try local repair, fall back to recompute."""
    u, v = edge
    ordering = state['ordering']

    # Try local repair
    new_order = _try_repair_delete(graph, ordering, u, v)
    if new_order is not None:
        return {'ordering': new_order, 'n': state['n']}

    # Fallback: full recompute
    new_order = _lexbfs(graph)
    return {'ordering': new_order, 'n': state['n']}
