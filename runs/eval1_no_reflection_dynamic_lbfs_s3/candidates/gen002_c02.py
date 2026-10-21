"""Dynamic LexBFS ordering (candidate gen002_c02).

Maintains a valid LexBFS ordering under edge insertions and deletions.

Strategy:
  1. After each update, check if the current ordering still satisfies
     the (LB) 4-point property (Corneil & Krueger certificate).
  2. If valid, return it unchanged (no recompute).
  3. If invalid, try targeted local repairs (move one of the vertices
     in the first violating triple).
  4. If local repair fails, fall back to a full static LexBFS
     recomputation via partition refinement.

The static LexBFS uses the standard partition-refinement algorithm
(Habib, McConnell, Paul, Viennot).  Tie-break: first element of the
first bucket (deterministic, valid for any LexBFS).
"""


def _static_lexbfs(graph):
    """Compute a valid LexBFS ordering from scratch via partition refinement.

    Returns a list of vertices in LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    # Buckets: list of lists of vertices (all with the same label).
    # Initially one bucket with all vertices in id order.
    buckets = [[v for v in range(n)]]
    ordering = []

    while buckets:
        # Pick the first bucket, take its first vertex.
        b0 = buckets[0]
        x = b0[0]
        ordering.append(x)

        # Remove x from its bucket.
        b0.pop(0)
        if not b0:
            buckets.pop(0)

        # Refine every remaining bucket by adjacency to x:
        # split into (neighbors of x, non-neighbors of x), preserving order.
        new_buckets = []
        for b in buckets:
            nb = [v for v in b if graph[x][v]]
            nnb = [v for v in b if not graph[x][v]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets

    return ordering


def _check_lb_property(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c (by index in ordering) with
    ac in E and ab not in E, there must exist d < a with
    db in E and dc not in E.

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if graph[a][b]:
                continue  # ab in E: condition not triggered
            for k in range(j + 1, n):
                c = ordering[k]
                if not graph[a][c]:
                    continue  # ac not in E: condition not triggered
                # ac in E, ab not in E: need d < a with db in E, dc not in E
                found = False
                for d_idx in range(i):
                    d = ordering[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _check_lb_property_fast(graph, ordering):
    """Faster check of the (LB) 4-point property using bitsets.

    For each vertex v, precompute:
      - adj[v]: bitset of neighbors of v
      - pos[v]: position of v in the ordering

    For each triple (a, b, c) with a < b < c (by position),
    ac in E, ab not in E:
      need d < a with db in E and dc not in E.
      Equivalently: (adj[b] & ~adj[c] & prefix_mask[a]) != 0
      where prefix_mask[a] has bits set for all vertices at positions < pos[a].
    """
    n = len(ordering)
    if n == 0:
        return True

    # Build position map and prefix masks.
    pos = [0] * n
    for idx, v in enumerate(ordering):
        pos[v] = idx

    # prefix_mask[i] = bitset of vertices at positions < i
    prefix_masks = [0] * (n + 1)
    mask = 0
    for i in range(n):
        prefix_masks[i] = mask
        mask |= (1 << ordering[i])

    # Precompute adjacency bitsets.
    adj_bits = [0] * n
    for v in range(n):
        bits = 0
        row = graph[v]
        for w in range(n):
            if row[w]:
                bits |= (1 << w)
        adj_bits[v] = bits

    # For each a (by position i), check all b, c after it.
    for i in range(n):
        a = ordering[i]
        adj_a_bits = adj_bits[a]
        prefix_a = prefix_masks[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if (adj_a_bits >> b) & 1:
                continue  # ab in E: condition not triggered
            adj_b_bits = adj_bits[b]
            for k in range(j + 1, n):
                c = ordering[k]
                if not ((adj_a_bits >> c) & 1):
                    continue  # ac not in E: condition not triggered
                # Need d < a with db in E and dc not in E.
                # d must be in prefix_a, adjacent to b, not adjacent to c.
                if (adj_b_bits & ~adj_bits[c] & prefix_a) != 0:
                    continue  # found such d
                return False
    return True


def _try_local_repair(graph, ordering):
    """Try to repair the ordering locally after an edge update.

    Finds the first violating triple (a, b, c) and tries targeted
    single-vertex moves.  Returns a valid ordering if successful,
    None otherwise.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    # Find the first violation.
    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if graph[a][b]:
                continue
            for k in range(j + 1, n):
                c = ordering[k]
                if not graph[a][c]:
                    continue
                # Violation: ac in E, ab not in E, no d < a with db in E, dc not in E.
                # Try targeted moves to fix this violation.
                candidates = []

                # Move b to just before a.
                new_order = ordering[:i] + [b] + ordering[i:j] + ordering[j + 1:]
                candidates.append(new_order)

                # Move c to just before b.
                new_order = ordering[:j] + [c] + ordering[j:k] + ordering[k + 1:]
                candidates.append(new_order)

                # Move a to just after c.
                new_order = ordering[:i] + ordering[i + 1:k + 1] + [a] + ordering[k + 1:]
                candidates.append(new_order)

                # Move b to just after c.
                new_order = ordering[:j] + ordering[j:k + 1] + [b] + ordering[k + 1:]
                candidates.append(new_order)

                # Move c to just before a.
                new_order = ordering[:i] + [c] + ordering[i:j] + ordering[j:k] + ordering[k + 1:]
                candidates.append(new_order)

                # Move a to just before b.
                new_order = ordering[:i] + ordering[i + 1:j] + [a] + ordering[j:k + 1] + ordering[k + 1:]
                candidates.append(new_order)

                # Move a to just before c.
                new_order = ordering[:i] + ordering[i + 1:j] + ordering[j:k] + [a] + ordering[k:]
                candidates.append(new_order)

                # Move b to just before c.
                new_order = ordering[:j] + ordering[j + 1:k] + [b] + ordering[k:]
                candidates.append(new_order)

                # Move c to just after b.
                new_order = ordering[:j] + ordering[j + 1:k + 1] + [c] + ordering[k + 1:]
                candidates.append(new_order)

                # Move a to just after b.
                new_order = ordering[:i] + ordering[i + 1:j + 1] + [a] + ordering[j + 1:]
                candidates.append(new_order)

                # Move a to the front.
                new_order = [a] + ordering[:i] + ordering[i + 1:]
                candidates.append(new_order)

                # Move b to the front.
                new_order = [b] + ordering[:j] + ordering[j + 1:]
                candidates.append(new_order)

                # Move c to the front.
                new_order = [c] + ordering[:k] + ordering[k + 1:]
                candidates.append(new_order)

                for cand in candidates:
                    if _check_lb_property(graph, cand):
                        return cand

    # No violation found (shouldn't happen if called after a failed check)
    # or local repair failed.
    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    ordering = _static_lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle edge insertion (u, v)."""
    ordering = state['ordering']

    # Check if the current ordering is still valid.
    if _check_lb_property_fast(graph, ordering):
        return {'ordering': ordering}

    # Try local repair.
    repaired = _try_local_repair(graph, ordering)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute.
    ordering = _static_lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    """Handle edge deletion (u, v)."""
    ordering = state['ordering']

    # Check if the current ordering is still valid.
    if _check_lb_property_fast(graph, ordering):
        return {'ordering': ordering}

    # Try local repair.
    repaired = _try_local_repair(graph, ordering)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute.
    ordering = _static_lexbfs(graph)
    return {'ordering': ordering}
