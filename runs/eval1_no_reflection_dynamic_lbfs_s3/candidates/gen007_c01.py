"""Dynamic LexBFS ordering (candidate gen007_c01).

Maintains a valid LexBFS ordering under edge insertions and deletions.

Strategy:
  1. After each update, check if the current ordering still satisfies
     the (LB) 4-point property (Corneil & Krueger certificate).
  2. If valid, return it unchanged (no recompute).
  3. If invalid, run a bounded iterative local-repair loop: at each
     round, scan for a violating triple (a, b, c) and try targeted
     single-vertex moves (b before a, c before b, a after c, plus
     a few extra positions); accept the first move that restores
     validity; repeat for a few rounds.
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


def _first_violation(ordering, graph):
    """Return (i, j, k) of the first violating triple, or None."""
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
                for d_idx in range(i):
                    d = ordering[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        break
                else:
                    return (i, j, k)
    return None


def _try_local_repair(graph, ordering, max_rounds=6):
    """Bounded iterative local repair.

    Each round: find the first violating triple (a, b, c) and try a
    set of targeted single-vertex moves; accept the first move that
    restores the (LB) property.  Returns a valid ordering if
    successful, None otherwise.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    current = list(ordering)
    for _ in range(max_rounds):
        viol = _first_violation(current, graph)
        if viol is None:
            return current
        i, j, k = viol
        a, b, c = current[i], current[j], current[k]

        # Candidate moves: relocate one of a, b, c to a nearby
        # position.  Each candidate is (vertex, new_index) where the
        # vertex is removed from its current position and inserted at
        # new_index in the list after removal.
        moves = []
        # b before a
        moves.append((b, i))
        # c before b
        moves.append((c, j))
        # a after c
        moves.append((a, k + 1))
        # b after c
        moves.append((b, k + 1))
        # c after a
        moves.append((c, i + 1))
        # a before b (i.e. right after position i-1, before b's slot)
        moves.append((a, j))

        for v, pos in moves:
            old_idx = current.index(v)
            cand = current[:old_idx] + current[old_idx + 1:]
            # clamp insertion position
            p = max(0, min(pos, len(cand)))
            cand = cand[:p] + [v] + cand[p:]
            if _check_lb_property(graph, cand):
                current = cand
                break
        else:
            # No move fixed the first violation; try the next
            # violating triple in this round.
            # Simple approach: skip this triple by trying moves for
            # the next violation.  To keep it simple, give up on this
            # round and stop if we cannot progress.
            return None

    return current if _check_lb_property(graph, current) else None


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
