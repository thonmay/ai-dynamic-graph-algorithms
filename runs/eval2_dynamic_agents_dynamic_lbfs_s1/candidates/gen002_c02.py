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

    # The property: for all a < b < c with ac in E and ab not in E,
    #   exists d < a with db in E and dc not in E.
    for a in range(n):
        for b in range(a + 1, n):
            if b in adj[a]:
                continue  # ab in E, antecedent false
            for c in range(b + 1, n):
                if c not in adj[a]:
                    continue  # ac not in E, antecedent false
                # Need exists d < a with db in E and dc not in E.
                found = False
                for d in range(a):
                    if d in adj[b] and d not in adj[c]:
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
