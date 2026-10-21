"""Dynamic LexBFS ordering (candidate gen003_c01).

Maintains a valid LexBFS ordering under edge insertions and deletions.

Strategy (derived from gen002_c01, with a stronger local-repair phase):
  1. After each update, check if the current ordering still satisfies
     the (LB) 4-point property (Corneil & Krueger certificate).
  2. If valid, return it unchanged (no recompute).
  3. If invalid, try targeted local repairs:
       a. single-vertex moves (as in the parent),
       b. a bounded number of random shuffles of the ordering,
       c. a bounded number of random restarts of the static LexBFS
          (different start vertices / tie-breaks).
  4. If all local repairs fail, fall back to a full static LexBFS
     recomputation via partition refinement.

The static LexBFS uses the standard partition-refinement algorithm
(Habib, McConnell, Paul, Viennot).  Tie-break: first element of the
first bucket (deterministic, valid for any LexBFS).
"""

import random


def _static_lexbfs(graph, start=None, rng=None):
    """Compute a valid LexBFS ordering from scratch via partition refinement.

    Returns a list of vertices in LexBFS order.

    Parameters
    ----------
    graph : list of lists of 0/1
    start : int or None
        If given, the ordering must begin with this vertex.  If None,
        the first vertex in id order is used.
    rng : random.Random or None
        If given, used to randomise the initial bucket order (which
        changes the tie-break).  If None, deterministic id order.
    """
    n = len(graph)
    if n == 0:
        return []

    # Initial bucket: all vertices.  If a start vertex is given, it is
    # placed first; the rest are in id order (or shuffled if rng given).
    if start is not None:
        rest = [v for v in range(n) if v != start]
        if rng is not None:
            rng.shuffle(rest)
        buckets = [[start] + rest]
    else:
        rest = list(range(n))
        if rng is not None:
            rng.shuffle(rest)
        buckets = [rest]

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


def _try_local_repair(graph, ordering, seed):
    """Try to repair the ordering locally after an edge update.

    Tries, in order:
      1. targeted single-vertex moves based on the first violating triple,
      2. a bounded number of random shuffles of the ordering,
      3. a bounded number of random restarts of the static LexBFS
         (different start vertices / tie-breaks).

    Returns a valid ordering if successful, None otherwise.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    rng = random.Random(seed)

    # --- Phase 1: targeted single-vertex moves ---
    viol = _find_first_violation(graph, ordering)
    if viol is not None:
        i, j, k = viol
        candidates = []

        # Move b to just before a.
        candidates.append(ordering[:i] + [ordering[j]] + ordering[i:j] + ordering[j + 1:])

        # Move c to just before b.
        candidates.append(ordering[:j] + [ordering[k]] + ordering[j:k] + ordering[k + 1:])

        # Move a to just after c.
        candidates.append(ordering[:i] + ordering[i + 1:k + 1] + [ordering[i]] + ordering[k + 1:])

        # Also try moving b to just after c, and c to just after a.
        candidates.append(ordering[:j] + ordering[j:k + 1] + [ordering[j]] + ordering[k + 1:])
        candidates.append(ordering[:i] + ordering[i + 1:j + 1] + [ordering[i]] + ordering[j + 1:])

        for cand in candidates:
            if _check_lb_property(graph, cand):
                return cand

    # --- Phase 2: random shuffles of the current ordering ---
    # A random permutation is a valid LexBFS ordering only for very
    # special graphs (e.g. complete or empty), but it is cheap to try
    # a few and check.
    for _ in range(8):
        cand = list(ordering)
        rng.shuffle(cand)
        if _check_lb_property(graph, cand):
            return cand

    # --- Phase 3: random restarts of the static LexBFS ---
    # Different start vertices and tie-breaks can yield different
    # valid orderings.  Try a few random restarts.
    for _ in range(6):
        start = rng.randrange(n)
        cand = _static_lexbfs(graph, start=start, rng=rng)
        if _check_lb_property(graph, cand):
            return cand

    return None


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    ordering = _static_lexbfs(graph)
    return {'ordering': ordering}


def _handle_update(graph, state, seed):
    """Common logic for insert_edge and delete_edge."""
    ordering = state['ordering']

    # Check if the current ordering is still valid.
    if _check_lb_property(graph, ordering):
        return {'ordering': ordering}

    # Try local repair.
    repaired = _try_local_repair(graph, ordering, seed)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute.
    ordering = _static_lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle edge insertion (u, v)."""
    seed = hash((edge[0], edge[1], 'ins'))
    return _handle_update(graph, state, seed)


def delete_edge(graph, edge, state):
    """Handle edge deletion (u, v)."""
    seed = hash((edge[0], edge[1], 'del'))
    return _handle_update(graph, state, seed)
