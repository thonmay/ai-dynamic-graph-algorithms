"""Dynamic LexBFS ordering (candidate gen006_c01).

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


def _find_first_violation(graph, ordering):
    """Find the first violating triple (i, j, k) or return None.

    A violation is a triple of positions i < j < k with
    ac in E, ab not in E, and no d < a with db in E and dc not in E.
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
                # ac in E, ab not in E: need d < a with db in E, dc not in E
                found = False
                for d_idx in range(i):
                    d = ordering[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return (i, j, k)
    return None


def _try_local_repair(graph, ordering):
    """Try to repair the ordering locally after an edge update.

    Repeatedly finds the first violating triple (a, b, c) and tries
    targeted single-vertex moves to fix it.  Returns a valid ordering
    if successful, None otherwise.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    cur = list(ordering)
    # Bound the number of repair iterations to avoid infinite loops.
    for _ in range(3 * n):
        viol = _find_first_violation(graph, cur)
        if viol is None:
            return cur  # no violation, ordering is valid

        i, j, k = viol
        a, b, c = cur[i], cur[j], cur[k]

        # Candidate moves to fix this violation.
        candidates = []

        # Move b to just before a.
        candidates.append(cur[:i] + [b] + cur[i:j] + cur[j + 1:])

        # Move c to just before b.
        candidates.append(cur[:j] + [c] + cur[j:k] + cur[k + 1:])

        # Move a to just after c.
        candidates.append(cur[:i] + cur[i + 1:k + 1] + [a] + cur[k + 1:])

        # Move b to just before c.
        candidates.append(cur[:j] + cur[j:k] + [b] + cur[k:])

        # Move a to just before b.
        candidates.append(cur[:i] + cur[i + 1:j] + [a] + cur[j:])

        # Move c to just before a.
        candidates.append(cur[:i] + [c] + cur[i:j] + cur[j:k] + cur[k + 1:])

        # Move b to the position of its last non-neighbor among
        # vertices before a (a natural "correct" position).
        last_nnb = -1
        for t in range(i):
            if not graph[cur[t]][b]:
                last_nnb = t
        if last_nnb >= 0 and last_nnb != j:
            candidates.append(cur[:last_nnb + 1] + [b] + cur[last_nnb + 1:j] + cur[j + 1:])

        # Move c to the position of its last neighbor among vertices
        # before a (a natural "correct" position).
        last_nb = -1
        for t in range(i):
            if graph[cur[t]][c]:
                last_nb = t
        if last_nb >= 0 and last_nb != k:
            candidates.append(cur[:last_nb + 1] + [c] + cur[last_nb + 1:k] + cur[k + 1:])

        # Move a to the position of its last non-neighbor among
        # vertices before c (a natural "correct" position).
        last_nna = -1
        for t in range(k):
            if t != i and not graph[cur[t]][a]:
                last_nna = t
        if last_nna >= 0 and last_nna != i:
            rest = cur[:i] + cur[i + 1:k + 1]
            # position in 'rest' just after the vertex at original index last_nna
            pos = last_nna if last_nna < i else last_nna - 1
            candidates.append(rest[:pos + 1] + [a] + rest[pos + 1:])

        for cand in candidates:
            if _check_lb_property(graph, cand):
                cur = cand
                break
        else:
            return None  # no candidate fixed the first violation

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
