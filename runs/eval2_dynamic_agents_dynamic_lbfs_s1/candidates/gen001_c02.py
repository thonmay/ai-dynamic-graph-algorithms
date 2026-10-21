"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m).
- insert_edge(u,v): if the current ordering is still valid (checked via the
  (LB) 4-point property), keep it.  Otherwise recompute from scratch.
- delete_edge(u,v): if the current ordering is still valid, keep it.
  Otherwise recompute from scratch.

The validity check uses the (LB) 4-point property (Corneil-Krueger):

  For all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.

This property is necessary and sufficient for an ordering to be a valid
LexBFS ordering, so the check is exact.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns an ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # order: list of vertices already output
    order = []
    # buckets: list of sets of unprocessed vertices, in order
    buckets = [set(range(n))]

    for _ in range(n):
        # Pick the first vertex in the first non-empty bucket.
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        # Pick the smallest vertex in that bucket (deterministic tie-break).
        v = min(buckets[bi])
        buckets[bi].discard(v)
        order.append(v)

        # Refine: split each bucket by adjacency to v.
        # The neighbor part goes before the non-neighbor part.
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = set(x for x in b if graph[v][x])
            nnb = b - nb
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True iff the ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    # Precompute adjacency as sets for fast lookup.
    adj = [set() for _ in range(n)]
    for i in range(n):
        vi = ordering[i]
        for j in range(i + 1, n):
            vj = ordering[j]
            if graph[vi][vj]:
                adj[i].add(j)
                adj[j].add(i)

    # For each b, precompute N_b = {d < b : d in adj[b]} (neighbors of b before b).
    #
    # The property: for all b < c with c in adj[b],
    #   for all a < b with a not in adj[b] and c in adj[a],
    #     exists d < a with d in N_b and d not in adj[c].
    #
    # For a fixed (b, c) with c in adj[b], b < c:
    #   Let S = {a < b : a not in adj[b] and c in adj[a]}.
    #   For each a in S, we need: exists d in N_b with d < a and d not in adj[c].

    for b in range(n):
        # N_b: neighbors of b before b
        N_b = sorted(d for d in adj[b] if d < b)
        if not N_b:
            continue
        for c in range(b + 1, n):
            if c not in adj[b]:
                continue
            # bc in E, b < c.
            # For each a < b with a not in adj[b] and c in adj[a]:
            for a in range(b):
                if a in adj[b]:
                    continue  # ab in E, skip
                if c not in adj[a]:
                    continue  # ac not in E, skip
                # ac in E and ab not in E.
                # Need exists d < a with d in N_b and d not in adj[c].
                found = False
                for d in N_b:
                    if d >= a:
                        break
                    if d not in adj[c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
