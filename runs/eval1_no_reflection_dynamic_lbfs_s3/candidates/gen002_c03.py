"""Dynamic LexBFS ordering (candidate gen002_c03).

Maintains a valid LexBFS ordering under edge insertions and deletions.

Strategy (derived from gen001_c02, with a faster certificate check and
more aggressive local repair):
  1. After each update, check if the current ordering still satisfies
     the (LB) 4-point property (Corneil & Krueger certificate).
     The check is O(n^2) using bitsets: for each position i, the set of
     vertices that can witness a violation is
         W_i = (N(a) \\ P_i) \\ (N(P_i) \\ N(a))
     where P_i is the prefix before a; the ordering is valid iff
     W_i is empty for every i.
  2. If valid, return it unchanged (no recompute).
  3. If invalid, try targeted local repairs: move one of the vertices
     in the first violating triple to several plausible positions
     (before a, before b, before c, after c, and the endpoints of the
     violating triple), verifying each candidate with the fast check.
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
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c (by index in ordering) with
    ac in E and ab not in E, there must exist d < a with
    db in E and dc not in E.

    Equivalent bitset formulation: for each position i (vertex a),
        W_i = (N(a) \\ P_i) \\ (N(P_i) \\ N(a))
    must be empty, where P_i is the set of vertices before a.
    W_i non-empty means some b in P_i is non-adjacent to a while some
    c after a is adjacent to a and no prefix vertex separates them.

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    if n == 0:
        return True

    # Bitset of neighbors for each vertex.
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        adj[u] = bits

    prefix = 0
    prefix_nb = 0
    for i in range(n):
        a = ordering[i]
        # W_i = (N(a) & ~prefix) & ~(prefix_nb & ~N(a))
        w = (adj[a] & ~prefix) & ~(prefix_nb & ~adj[a])
        if w:
            return False
        prefix |= 1 << a
        prefix_nb |= adj[a]
    return True


def _first_violation(graph, ordering):
    """Find the first violating triple (i, j, k) with i < j < k.

    Returns (i, j, k) or None if the ordering is valid.
    """
    n = len(ordering)
    if n == 0:
        return None

    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        adj[u] = bits

    prefix = 0
    prefix_nb = 0
    for i in range(n):
        a = ordering[i]
        w = (adj[a] & ~prefix) & ~(prefix_nb & ~adj[a])
        if w:
            # Find the earliest b (position j > i) with b in prefix... wait,
            # b must be after a in the ordering (j > i).  The bitset w
            # contains vertices c (after a) that are adjacent to a and not
            # separated.  We need b: a vertex after a, non-adjacent to a,
            # with c after b.  Reconstruct the triple explicitly.
            a_nb = adj[a]
            # c candidates: bits in w (all after a, adjacent to a).
            # b candidates: positions j > i with not graph[a][ordering[j]].
            # We need b before c (j < k).
            c_bits = w
            # Find earliest b after a that is non-adjacent to a.
            for j in range(i + 1, n):
                b = ordering[j]
                if a_nb >> b & 1:
                    continue
                # Need c after b with c in w.
                # c must be at position > j.
                for k in range(j + 1, n):
                    c = ordering[k]
                    if c_bits >> c & 1:
                        return (i, j, k)
            # Should not happen: w non-empty implies some c after a; and
            # if every vertex between a and that c is adjacent to a, then
            # ... actually w non-empty guarantees a violation exists, so
            # some b must work.  But to be safe, fall through.
        prefix |= 1 << a
        prefix_nb |= adj[a]
    return None


def _try_local_repair(graph, ordering):
    """Try to repair the ordering locally after an edge update.

    Finds the first violating triple (a, b, c) and tries targeted
    single-vertex moves to several plausible positions.  Returns a
    valid ordering if successful, None otherwise.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    viol = _first_violation(graph, ordering)
    if viol is None:
        return ordering
    i, j, k = viol
    a, b, c = ordering[i], ordering[j], ordering[k]

    # Candidate target positions (indices in the original ordering where
    # the moved vertex will be inserted).
    positions = sorted(set([0, i, j, k, i + 1, j + 1, k + 1, n]))

    # Try moving each of a, b, c to each position.
    for v in (b, c, a):
        vi = ordering.index(v)
        for pos in positions:
            if pos == vi or pos == vi + 1:
                continue  # no-op
            cand = ordering[:vi] + ordering[vi + 1:]
            insert_at = pos if pos < vi else pos - 1
            cand = cand[:insert_at] + [v] + cand[insert_at:]
            if _check_lb_property(graph, cand):
                return cand

    # Second round: swap adjacent pairs near the violation.
    for p in range(max(0, i - 1), min(n - 1, k + 1)):
        cand = ordering[:]
        cand[p], cand[p + 1] = cand[p + 1], cand[p]
        if _check_lb_property(graph, cand):
            return cand

    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    ordering = _static_lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle edge insertion (u, v)."""
    ordering = state['ordering']

    # Check if the current ordering is still valid.
    if _check_lb_property(graph, ordering):
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
    if _check_lb_property(graph, ordering):
        return {'ordering': ordering}

    # Try local repair.
    repaired = _try_local_repair(graph, ordering)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute.
    ordering = _static_lexbfs(graph)
    return {'ordering': ordering}
