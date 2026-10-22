"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try to
repair the existing ordering locally:

  * Edge insertion (u, v): if the ordering is already valid, keep it.
    Otherwise, try moving u to the front, or moving v to the front.
    If either yields a valid ordering, use it.
  * Edge deletion: if the ordering is still valid, keep it. Otherwise
    fall back to a full recompute.

If the local repair fails, fall back to a full O(n^2) bitset-based
partition-refinement LexBFS recompute.

Correctness: every returned ordering is either (a) the previous ordering
which we have verified is still a valid LexBFS ordering of the current
graph, or (b) a freshly computed LexBFS ordering of the current graph.
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
    """Check the (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, there exists d < a with db in E and dc not in E.

    adj: list of int bitsets, adj[x] has bit y set iff (x, y) in E.
    Returns True iff ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # Build prefix bitsets: pref[i] = bits of ordering[0..i-1]
    pref = [0] * (n + 1)
    for i in range(n):
        pref[i + 1] = pref[i] | (1 << ordering[i])
    all_bits = (1 << n) - 1

    for i in range(n):
        a = ordering[i]
        Na = adj[a]
        before_a = pref[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if (Na >> b) & 1:
                continue  # ab in E, no constraint
            # ab not in E
            after_j = all_bits ^ (pref[j + 1] | (1 << b))
            bad_c = Na & after_j
            if bad_c == 0:
                continue
            good_d = adj[b] & before_a
            # For each c in bad_c, need good_d & ~adj[c] != 0
            bc = bad_c
            while bc:
                lsb = bc & (-bc)
                c = lsb.bit_length() - 1
                if good_d & ~adj[c] == 0:
                    return False
                bc ^= lsb
    return True


def _try_repair_insertion(ordering, u, v, adj):
    """Try to repair the ordering after inserting edge (u, v).

    If the ordering is already valid, return it unchanged.
    Otherwise, try moving u to the front, or moving v to the front.
    If either yields a valid ordering, return it.
    Otherwise return None.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    # First check if already valid
    if _is_valid_lexbfs(ordering, adj):
        return ordering

    # Try moving u to front
    new_order = [u] + [x for x in ordering if x != u]
    if _is_valid_lexbfs(new_order, adj):
        return new_order

    # Try moving v to front
    new_order = [v] + [x for x in ordering if x != v]
    if _is_valid_lexbfs(new_order, adj):
        return new_order

    return None


def init(graph):
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = _build_adj_bitsets(graph)

    repaired = _try_repair_insertion(ordering, u, v, adj)
    if repaired is not None:
        return {'ordering': repaired}

    # Fall back to full recompute
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    adj = _build_adj_bitsets(graph)

    # Check if the ordering is still valid after deletion
    if _is_valid_lexbfs(ordering, adj):
        return {'ordering': ordering}

    # Fall back to full recompute
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}
