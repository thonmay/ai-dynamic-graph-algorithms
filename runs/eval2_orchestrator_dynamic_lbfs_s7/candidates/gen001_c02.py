"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge(u, v): if the current ordering is still a valid LexBFS ordering of
  the new graph, keep it (no work beyond the O(n^3) validity check).  Otherwise
  recompute from scratch.
- delete_edge(u, v): edge deletions CAN invalidate a LexBFS ordering (removing
  a witness edge can create a new violation).  So we check validity and
  recompute if needed.

The (LB) 4-point property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs_clean(graph):
    """Static LexBFS via partition refinement. Returns the ordering list."""
    n = len(graph)
    if n == 0:
        return []
    # buckets: list of lists of vertices, in current order
    buckets = [[v] for v in range(n)]
    # for each vertex, the index of the bucket it currently lives in
    bucket_of = list(range(n))
    # for each vertex, the index of the first bucket that contains a neighbour
    first = [n] * n
    processed = [False] * n
    ordering = []

    for step in range(n):
        # pick the unprocessed vertex with the lexicographically smallest label
        best = None
        for v in range(n):
            if processed[v]:
                continue
            key = (first[v], v)
            if best is None or key < (first[best], best):
                best = v
        x = best
        processed[x] = True
        ordering.append(x)
        # refine: split every bucket by adjacency to x
        new_buckets = []
        for b in buckets:
            nb = [v for v in b if graph[v][x]]
            nnb = [v for v in b if not graph[v][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets
        # update bookkeeping
        for i, b in enumerate(buckets):
            for v in b:
                bucket_of[v] = i
        for v in range(n):
            if graph[v][x]:
                first[v] = bucket_of[v]
            else:
                first[v] = n

    return ordering


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property. Returns True if ordering is a valid
    LexBFS ordering of graph.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    O(n^3) algorithm:
    For each c, precompute for each a < c with ac in E, the set of
    d < a with dc not in E (witness pool). Then for each b in (a, c)
    with ab not in E, check if witness_pool intersects adj[b].
    """
    n = len(graph)
    if n <= 2:
        return True

    # Precompute adjacency as sets for fast lookup
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    for c in range(n):
        vc = ordering[c]
        # For each a < c with ac in E
        for a in range(c):
            va = ordering[a]
            if va not in adj[vc]:
                continue
            # ac in E
            # Precompute witness pool: d at position < a with dc not in E
            witness_pool = set()
            for d_pos in range(a):
                vd = ordering[d_pos]
                if vd not in adj[vc]:
                    witness_pool.add(vd)
            if not witness_pool:
                # No possible witness for any b in (a, c)
                # Check if there's any b in (a, c) with ab not in E
                for b in range(a + 1, c):
                    vb = ordering[b]
                    if vb not in adj[va]:
                        return False
                continue
            # For each b in (a, c) with ab not in E, check if
            # witness_pool intersects adj[b]
            for b in range(a + 1, c):
                vb = ordering[b]
                if vb in adj[va]:
                    continue
                # ab not in E, need witness
                # Check if any d in witness_pool has db in E
                found = False
                for d in witness_pool:
                    if vb in adj[d]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs_clean(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    # Check if the current ordering is still valid
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Otherwise recompute
    ordering = _lexbfs_clean(graph)
    return {'ordering': ordering, 'n': state['n']}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    # Edge deletions CAN invalidate a LexBFS ordering
    if _is_valid_lexbfs(graph, ordering):
        return state
    ordering = _lexbfs_clean(graph)
    return {'ordering': ordering, 'n': state['n']}
