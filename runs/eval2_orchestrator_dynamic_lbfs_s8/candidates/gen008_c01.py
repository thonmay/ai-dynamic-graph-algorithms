"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try to
repair the existing ordering locally:

  * Edge insertion (u, v): if the old ordering is still valid (checked via
    the (LB) 4-point property of Corneil and Krueger), keep it. Otherwise
    recompute from scratch.
  * Edge deletion (u, v): the deleted edge may have been the witness
    "db in E" for some (LB) triple, so the old ordering can become invalid.
    Check the (LB) property; recompute if violated.

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.

Both insertion and deletion checks are O(n^3) worst case (same order as a
full recompute) but typically much cheaper: the check stops at the first
violation, and for many updates the old ordering remains valid.
"""


def _build_adj_bitsets(graph):
    """Build adjacency as Python int bitsets."""
    n = len(graph)
    adj = [0] * n
    for i in range(n):
        row = graph[i]
        bits = 0
        for j in range(n):
            if row[j]:
                bits |= (1 << j)
        adj[i] = bits
    return adj


def _lexbfs_static(graph):
    """Compute a LexBFS ordering using partition refinement with bitsets.
    O(n^2) time. Returns a list of n vertices in LexBFS order."""
    n = len(graph)
    if n == 0:
        return []
    if n == 1:
        return [0]

    adj = _build_adj_bitsets(graph)

    # P: list of bitsets (blocks), in order.
    # Start with one block containing all vertices.
    P = [(1 << n) - 1]
    ordering = []

    for _ in range(n):
        # Find first non-empty block
        idx = 0
        while idx < len(P) and P[idx] == 0:
            idx += 1
        if idx >= len(P):
            break

        # Pick a vertex from P[idx] (lowest set bit for determinism)
        block = P[idx]
        v = (block & (-block)).bit_length() - 1
        P[idx] = block & ~(1 << v)
        ordering.append(v)

        # Refine all blocks by adjacency to v
        new_P = []
        for b in P:
            if b == 0:
                continue
            b1 = b & adj[v]   # neighbors of v
            b2 = b & ~adj[v]  # non-neighbors of v
            if b1:
                new_P.append(b1)
            if b2:
                new_P.append(b2)
        P = new_P

    return ordering


def _is_valid_lexbfs(ordering, adj):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True iff the ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    for a in range(n):
        va = ordering[a]
        adj_a = adj[va]
        for b in range(a + 1, n):
            vb = ordering[b]
            if adj_a >> vb & 1:
                continue  # ab in E, no constraint
            # ab not in E: for every c > b with ac in E, need d < a
            # with db in E and dc not in E.
            adj_b = adj[vb]
            for c in range(b + 1, n):
                vc = ordering[c]
                if not (adj_a >> vc & 1):
                    continue  # ac not in E, no constraint
                # Need d < a with db in E and dc not in E.
                adj_c = adj[vc]
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if (adj_b >> vd & 1) and not (adj_c >> vd & 1):
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    ordering = _lexbfs_static(graph)
    adj = _build_adj_bitsets(graph)
    return {'ordering': ordering, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']

    # Update adj bitsets
    adj[u] |= (1 << v)
    adj[v] |= (1 << u)

    # Check if the old ordering is still valid
    if _is_valid_lexbfs(ordering, adj):
        return {'ordering': ordering, 'adj': adj}

    # Otherwise recompute
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']

    # Update adj bitsets
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)

    # Deleting an edge CAN create a (LB) violation: the deleted edge may
    # have been the witness db in E for some triple (a, b, c).
    # Check validity; recompute if needed.
    if _is_valid_lexbfs(ordering, adj):
        return {'ordering': ordering, 'adj': adj}

    ordering = _lexbfs_static(graph)
    return {'ordering': ordering, 'adj': adj}
