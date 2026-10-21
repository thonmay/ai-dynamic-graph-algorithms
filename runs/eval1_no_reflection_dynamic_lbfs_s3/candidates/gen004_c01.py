"""Dynamic LexBFS ordering (candidate gen004_c01).

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


def _count_violations(graph, ordering):
    """Count the number of violating triples (a, b, c) with i < j < k,
    ac in E, ab not in E, and no d < a with db in E and dc not in E.
    """
    n = len(ordering)
    count = 0
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
                found = False
                for d_idx in range(i):
                    d = ordering[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    count += 1
    return count


def _try_local_repair(graph, ordering):
    """Try to repair the ordering locally after an edge update.

    Greedy local search: repeatedly find the first violating triple
    and try all single-vertex moves (move any vertex to any position),
    accepting the first move that strictly reduces the total number of
    violations.  Returns a valid ordering if successful, None otherwise.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    cur = list(ordering)
    cur_count = _count_violations(graph, cur)
    if cur_count == 0:
        return cur

    # Bounded number of improvement steps to avoid long loops.
    max_steps = 4 * n
    for _ in range(max_steps):
        # Find the first violating triple (i, j, k).
        first_viol = None
        for i in range(n):
            a = cur[i]
            for j in range(i + 1, n):
                b = cur[j]
                if graph[a][b]:
                    continue
                for k in range(j + 1, n):
                    c = cur[k]
                    if not graph[a][c]:
                        continue
                    found = False
                    for d_idx in range(i):
                        d = cur[d_idx]
                        if graph[d][b] and not graph[d][c]:
                            found = True
                            break
                    if not found:
                        first_viol = (i, j, k)
                        break
                if first_viol is not None:
                    break
            if first_viol is not None:
                break

        if first_viol is None:
            return cur  # no violations left

        # Try all single-vertex moves: move vertex at position p to
        # position q (q != p).  Accept the first move that reduces
        # the total violation count.
        best_move = None
        best_count = cur_count
        for p in range(n):
            v = cur[p]
            rest = cur[:p] + cur[p + 1:]
            for q in range(n):
                if q == p:
                    continue
                cand = rest[:q] + [v] + rest[q:]
                cnt = _count_violations(graph, cand)
                if cnt < best_count:
                    best_count = cnt
                    best_move = cand
                    if cnt == 0:
                        break
            if best_count == 0:
                break

        if best_move is None:
            return None  # stuck in a local minimum

        cur = best_move
        cur_count = best_count
        if cur_count == 0:
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
