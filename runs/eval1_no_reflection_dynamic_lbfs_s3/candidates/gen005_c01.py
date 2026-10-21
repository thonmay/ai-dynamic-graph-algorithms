"""Dynamic LexBFS ordering (candidate gen005_c01).

Maintains a valid LexBFS ordering under edge insertions and deletions.

Strategy:
  1. After each update, check if the current ordering still satisfies
     the (LB) 4-point property (Corneil & Krueger certificate).
  2. If valid, return it unchanged (no recompute).
  3. If invalid, try bounded local repair: repeatedly find the first
     violating triple and try all single-vertex moves (move any vertex
     to any position) that fix the first violation, accepting the
     first candidate that passes the full (LB) check.  This is far
     cheaper than a full recompute and handles more cases than the
     parent's three fixed moves.
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


def _first_violation(graph, ordering):
    """Return (i, j, k) of the first violating triple, or None.

    A violation is a triple of positions i < j < k with
    ac in E, ab not in E, and no d < i with db in E and dc not in E.
    """
    n = len(ordering)
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
                # ac in E, ab not in E: need d < i with db in E, dc not in E
                found = False
                for d_idx in range(i):
                    d = ordering[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return (i, j, k)
    return None


def _try_local_repair(graph, ordering, max_rounds=8):
    """Try to repair the ordering locally after an edge update.

    Repeatedly finds the first violating triple and tries all
    single-vertex moves (move any vertex to any position) that fix
    the first violation, accepting the first candidate that passes
    the full (LB) check.  Returns a valid ordering if successful,
    None otherwise.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    cur = ordering
    for _ in range(max_rounds):
        viol = _first_violation(graph, cur)
        if viol is None:
            return cur
        i, j, k = viol

        # Generate candidate moves: move any vertex to any position.
        # To keep this cheap, only consider moves that plausibly fix
        # the first violation: move b (position j) or c (position k)
        # to an earlier position, or move a (position i) to a later
        # position.  We try all such moves.
        tried = set()
        candidates = []

        # Move b (at position j) to any position p in [0, j).
        for p in range(j):
            if p == i:
                continue
            v = cur[j]
            new_order = cur[:p] + [v] + cur[p:j] + cur[j + 1:]
            key = ('b', p)
            if key not in tried:
                tried.add(key)
                candidates.append(new_order)

        # Move c (at position k) to any position p in [0, k).
        for p in range(k):
            if p == i or p == j:
                continue
            v = cur[k]
            new_order = cur[:p] + [v] + cur[p:k] + cur[k + 1:]
            key = ('c', p)
            if key not in tried:
                tried.add(key)
                candidates.append(new_order)

        # Move a (at position i) to any position p in (i, n).
        for p in range(i + 1, n):
            v = cur[i]
            new_order = cur[:i] + cur[i + 1:p + 1] + [v] + cur[p + 1:]
            key = ('a', p)
            if key not in tried:
                tried.add(key)
                candidates.append(new_order)

        # Try each candidate; accept the first that passes the full check.
        for cand in candidates:
            if _check_lb_property(graph, cand):
                cur = cand
                break
        else:
            # No single move fixed the first violation; give up.
            return None

    # Exhausted rounds; check if we ended up valid.
    if _check_lb_property(graph, cur):
        return cur
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
