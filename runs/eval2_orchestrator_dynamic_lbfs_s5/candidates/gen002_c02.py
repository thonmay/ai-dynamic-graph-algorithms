"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder a small window of the ordering). If the local
repair fails, fall back to a full recomputation of a LexBFS ordering from
scratch.

The (LB) 4-point property (Corneil & Krueger): for all positions
a < b < c with ac in E and ab not in E, there exists d < a with
db in E and dc not in E.

IMPORTANT: the (LB) property is a necessary condition for a LexBFS ordering
but NOT a sufficient certificate (it characterizes chordal graphs, not
LexBFS orderings of arbitrary graphs). Therefore the local-repair fast path
validates each candidate with a sound certificate: the candidate must be
accepted by a proper LexBFS validity check (see _is_lexbfs_ordering), which
verifies the prefix-label invariant that characterizes exactly the orderings
some LexBFS run can produce.
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


def _is_lexbfs_ordering(ordering, adj, n):
    """Sound certificate: is `ordering` a valid LexBFS ordering of `adj`?

    An ordering is a LexBFS ordering iff for every prefix of the ordering,
    the next vertex in the ordering has a lexicographically maximal
    adjacency-pattern label (to the prefix, read in output order) among all
    remaining vertices.

    This is exactly the invariant maintained by the HMPV partition-refinement
    LexBFS, so it is a necessary and sufficient condition for the ordering
    to be producible by some LexBFS run (with any tie-break).
    """
    if n == 0:
        return True
    if len(ordering) != n or sorted(ordering) != list(range(n)):
        return False

    # pos[v] = index in ordering
    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    # label[v] = tuple of bits adj[v][ordering[k]] for k < pos[v].
    # label_a < label_b iff at the first position k where they differ
    # (k < min(pos[a], pos[b])), adj[a][ordering[k]] < adj[b][ordering[k]];
    # if one label is a prefix of the other, the shorter is smaller.

    def label_less(a, b):
        """True if label[a] < label[b] lexicographically."""
        pa, pb = pos[a], pos[b]
        m = pa if pa < pb else pb
        for k in range(m):
            va = adj[a][ordering[k]]
            vb = adj[b][ordering[k]]
            if va != vb:
                return va < vb
        # equal up to min length; shorter label is lexicographically smaller
        return pa < pb

    for i in range(n):
        x = ordering[i]
        # x must have a lexicographically maximal label among remaining
        # vertices (positions i..n-1).
        for j in range(i + 1, n):
            y = ordering[j]
            # if label[y] > label[x], x is not maximal -> invalid
            if not label_less(y, x):
                return False
    return True


def _check_lb_property(ordering, adj, n):
    """Check the (LB) 4-point property.

    For all positions a < b < c (positions in the ordering) with
    ac in E and ab not in E, there exists d < a with
    db in E and dc not in E.

    Returns True if valid, False otherwise.

    NOTE: this is a necessary condition for a LexBFS ordering but not a
    sufficient one. It is kept only as a cheap pre-filter for the local
    repair; final acceptance uses _is_lexbfs_ordering.
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

    A candidate is accepted only if it passes the sound LexBFS certificate
    (_is_lexbfs_ordering). The (LB) property is used as a cheap pre-filter.
    """
    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    candidates = []

    # The unchanged ordering itself is a candidate (the update may not
    # have broken LexBFS validity).
    candidates.append(ordering[:])

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

    # Check each candidate: sound certificate only. The (LB) property is a
    # necessary condition for a LexBFS ordering but NOT a sufficient one, so
    # it must not be used as an acceptance test (it would accept orderings
    # that no LexBFS run can produce).
    for cand in candidates:
        if _is_lexbfs_ordering(cand, adj, n):
            return cand

    return None


def _debug_trace():
    """Manual trace of the failing case (triangle -> insert (0,1))."""
    # init on triangle: _lexbfs_ordering returns [0,1,2]
    # insert (0,1) on graph with edge (0,1) present:
    # old ordering [0,1,2], new graph = triangle
    # candidate [0,1,2]: _is_lexbfs_ordering should return True
    adj = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]
    ordering = [0, 1, 2]
    n = 3
    print("is_lexbfs:", _is_lexbfs_ordering(ordering, adj, n))
    print("lb_property:", _check_lb_property(ordering, adj, n))
    # Check label comparisons
    pos = [0, 1, 2]
    for i in range(n):
        x = ordering[i]
        for j in range(i + 1, n):
            y = ordering[j]
            pa, pb = pos[x], pos[y]
            m = min(pa, pb)
            bits_x = [adj[x][ordering[k]] for k in range(m)]
            bits_y = [adj[y][ordering[k]] for k in range(m)]
            print(f"  x={x} y={y} pa={pa} pb={pb} bits_x={bits_x} bits_y={bits_y}")


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
