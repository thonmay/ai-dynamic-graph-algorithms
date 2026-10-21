"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge(u,v): if the current ordering is still valid (checked via the
  (LB) 4-point property), keep it.  Otherwise recompute.
- delete_edge(u,v): if the current ordering is still valid, keep it.
  Otherwise recompute.

The validity check uses the (LB) 4-point property of Corneil and Krueger:
  for all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.

Implementation notes:
- Adjacency is cached in the state as Python int bitmasks (one per vertex),
  so the check runs in O(n^3 / word) instead of O(n^4).
- The check is exact: an ordering is a valid LexBFS ordering iff it satisfies
  (LB), so returning the old ordering when the check passes is always correct.
"""


def _adj_masks(graph):
    """Build adjacency as a list of int bitmasks."""
    n = len(graph)
    masks = [0] * n
    for i in range(n):
        row = graph[i]
        m = 0
        for j in range(n):
            if row[j]:
                m |= 1 << j
        masks[i] = m
    return masks


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    adj = _adj_masks(graph)

    # Partition refinement LexBFS.
    # P is a list of sets (the current partition), ordered.
    P = [set(range(n))]
    order = []

    while P:
        # Take the first bucket
        S = P[0]
        if not S:
            P.pop(0)
            continue
        # Pick the first vertex (smallest id for determinism)
        v = min(S)
        S.remove(v)
        order.append(v)

        # Split S by N(v)
        if S:
            S1 = {x for x in S if (adj[v] >> x) & 1}
            S2 = S - S1
            new_buckets = []
            if S1:
                new_buckets.append(S1)
            if S2:
                new_buckets.append(S2)
            P[0:1] = new_buckets

        # Split all other buckets by N(v)
        for i in range(1, len(P)):
            T = P[i]
            T1 = {x for x in T if (adj[v] >> x) & 1}
            T2 = T - T1
            new_buckets = []
            if T1:
                new_buckets.append(T1)
            if T2:
                new_buckets.append(T2)
            P[i:i+1] = new_buckets

    return order


def _is_valid_lexbfs(ordering, adj):
    """Check if ordering is a valid LexBFS ordering using the (LB) property.

    (LB): for all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    adj: list of int bitmasks, adj[x] has bit y set iff xy in E.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # prefix[i] = bitmask of vertices at positions < i
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << ordering[i])

    all_mask = (1 << n) - 1

    # For each pair of positions (a, b) with a < b and ab not in E:
    #   C = {c : pos[c] > b, ac in E}
    #   if C is non-empty, we need: for every c in C,
    #       exists d with pos[d] < a, db in E, dc not in E.
    #   i.e., D = adj[b] & prefix[a] is not a subset of adj[c].
    #   Equivalently: D is not a subset of (intersection of adj[c] over c in C).
    #   So: if D & ~I == 0 for I = intersection of adj[c] over c in C, fail.

    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if (adj[va] >> vb) & 1:
                continue  # ab in E, no constraint
            # ab not in E
            # C = neighbors of va at positions > b
            C = adj[va] & (all_mask ^ prefix[b + 1])
            if not C:
                continue
            # D = neighbors of vb at positions < a
            D = adj[vb] & prefix[a]
            if not D:
                # No d before a adjacent to b, so for any c in C,
                # we need d < a with db in E and dc not in E.
                # But D is empty, so no such d exists. Fail.
                return False
            # For each c in C, check D not subset of adj[c].
            # Equivalently: D is not a subset of (intersection of adj[c] over c in C).
            # Compute I = intersection of adj[c] for c in C.
            I = all_mask
            c = C
            while c:
                lb = c & (-c)
                c ^= lb
                ci = lb.bit_length() - 1
                I &= adj[ci]
                # Early exit: if D & ~I != 0, then D is not a subset of I,
                # which means there exists d in D not in I. Since I is the
                # intersection so far, d is not in adj[ci] for some ci processed.
                # But we need D not subset of adj[c] for ALL c in C.
                # If D & ~I != 0 at any point, it means for the current ci,
                # there's a d in D not in adj[ci]. But we need this for ALL c.
                # Actually, the condition is: for ALL c in C, D & ~adj[c] != 0.
                # This is equivalent to: D & ~(intersection of adj[c] over c in C) != 0.
                # So we just need to compute the full intersection and check.
                # We can't early-exit on D & ~I != 0 because I is still shrinking.
                # But we CAN early-exit if I becomes 0 (then D & ~I = D != 0, pass).
                if not I:
                    break
            # After the loop, check D & ~I
            if not (D & ~I):
                return False
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    adj = _adj_masks(graph)
    return {'ordering': ordering, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']
    # Update adj for the new edge
    adj[u] |= (1 << v)
    adj[v] |= (1 << u)
    # Check if current ordering is still valid
    if _is_valid_lexbfs(ordering, adj):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    adj = _adj_masks(graph)
    return {'ordering': ordering, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    adj = state['adj']
    # Update adj for the removed edge
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    # Check if current ordering is still valid
    if _is_valid_lexbfs(ordering, adj):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    adj = _adj_masks(graph)
    return {'ordering': ordering, 'adj': adj}
