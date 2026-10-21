"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge(u, v): if the ordering is already valid for the new graph,
  keep it (cheap check). Otherwise recompute.
- delete_edge(u, v): if the ordering is still valid for the new graph,
  keep it. Otherwise recompute.

The validity check uses the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

The check is O(n^3) in the worst case but early-exits on the first
violation, so it is fast when the ordering is still valid.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # Each vertex has a label: a list of (bucket_id, position_in_bucket)
    # We use the standard LexBFS algorithm.
    #
    # Maintain a list of buckets (each a list of vertices).
    # Initially one bucket with all vertices.
    # At each step, pick the first non-empty bucket, take its first vertex,
    # output it, then refine all buckets by adjacency to that vertex.

    # For efficiency, we track for each vertex its current bucket and
    # position within the bucket.

    # buckets: list of lists of vertices
    # We'll use a simpler approach: maintain labels as lists of 0/1
    # (adjacency to previously selected vertices, in order).

    # Actually, let's use the standard approach with buckets.
    # Each bucket is a list. When we select a vertex v from bucket B,
    # we split every bucket into (neighbors of v, non-neighbors of v).

    # For n up to a few hundred, O(n^2) is fine.

    # Simple O(n^2) LexBFS:
    # Maintain an ordering of unselected vertices.
    # Each unselected vertex has a label (list of 0/1, one per selected vertex).
    # At each step, pick the unselected vertex with the lexicographically
    # smallest label (ties broken by vertex id for determinism, but any
    # tie-break is valid).

    # Actually, the standard LexBFS: labels are compared lexicographically,
    # and we pick the vertex with the smallest label. Ties can be broken
    # arbitrarily.

    # Let's use the bucket-based approach for clarity.

    # buckets: list of lists of unselected vertices
    # Initially: one bucket with all vertices
    buckets = [list(range(n))]
    selected = [False] * n
    ordering = []

    for _ in range(n):
        # Find the first non-empty bucket
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break

        # Take the first vertex from this bucket
        v = buckets[bi].pop(0)
        selected[v] = True
        ordering.append(v)

        # Refine all buckets: split each into (neighbors of v, non-neighbors)
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nbrs = [x for x in b if graph[v][x]]
            non_nbrs = [x for x in b if not graph[v][x]]
            if nbrs:
                new_buckets.append(nbrs)
            if non_nbrs:
                new_buckets.append(non_nbrs)
        buckets = new_buckets

    return ordering


def _is_valid_lexbfs(graph, ordering):
    """Check if ordering is a valid LexBFS ordering using the (LB) property.

    (LB): for all a < b < c (positions in ordering) with
    ac in E and ab not in E, there exists d < a with db in E and dc not in E.

    Returns True if valid.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # pos[v] = position of vertex v in ordering
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    # For the (LB) check:
    # For each pair (b, c) with pos[b] < pos[c]:
    #   For each a with pos[a] < pos[b] and graph[a][c] and not graph[a][b]:
    #     Need: exists d with pos[d] < pos[a] and graph[d][b] and not graph[d][c]

    # More efficient: for each b, c with pos[b] < pos[c]:
    #   Let A = {a : pos[a] < pos[b], graph[a][c]=1, graph[a][b]=0}
    #   If A is non-empty, let a_max = max pos[a] for a in A
    #   Need: exists d with pos[d] < a_max, graph[d][b]=1, graph[d][c]=0

    # Actually the property is: for ALL a < b < c with ac in E, ab not in E,
    # there exists d < a with db in E, dc not in E.

    # So for each triple (a, b, c) with pos[a] < pos[b] < pos[c],
    # graph[a][c] = 1, graph[a][b] = 0:
    #   need exists d with pos[d] < pos[a], graph[d][b] = 1, graph[d][c] = 0.

    # O(n^4) naive. Let's optimize.

    # For fixed b, c (pos[b] < pos[c]):
    #   For each a with pos[a] < pos[b], graph[a][c]=1, graph[a][b]=0:
    #     need exists d with pos[d] < pos[a], graph[d][b]=1, graph[d][c]=0.

    # Precompute for each pair (b, c) with pos[b] < pos[c]:
    #   For each position p < pos[b], check if vertex at position p has
    #   graph[p][b]=1 and graph[p][c]=0.

    # Let's do it as: for each b, c with pos[b] < pos[c]:
    #   Let good_d = set of positions d < pos[b] where graph[ordering[d]][b]=1 and graph[ordering[d]][c]=0
    #   For each a with pos[a] < pos[b], graph[a][c]=1, graph[a][b]=0:
    #     need min(good_d) < pos[a]  (i.e., exists d in good_d with d < pos[a])

    # Actually we need d < a (position), so we need the minimum position in good_d
    # to be < pos[a].

    # Let's precompute for each (b, c): the minimum position d < pos[b]
    # with graph[ordering[d]][b]=1 and graph[ordering[d]][c]=0.
    # If no such d exists, min_d = infinity.
    # Then for each a with pos[a] < pos[b], graph[a][c]=1, graph[a][b]=0:
    #   need min_d < pos[a].

    # This is O(n^3) total.

    for bi in range(n):
        b = ordering[bi]
        for ci in range(bi + 1, n):
            c = ordering[ci]
            # Find min position d < bi with graph[ordering[d]][b]=1 and graph[ordering[d]][c]=0
            min_d = n  # infinity
            for di in range(bi):
                d = ordering[di]
                if graph[d][b] and not graph[d][c]:
                    min_d = di
                    break
            if min_d == n:
                # No such d exists. Check if there's any a with pos[a] < bi,
                # graph[a][c]=1, graph[a][b]=0.
                for ai in range(bi):
                    a = ordering[ai]
                    if graph[a][c] and not graph[a][b]:
                        return False
            else:
                # For each a with pos[a] < bi, graph[a][c]=1, graph[a][b]=0:
                # need min_d < pos[a], i.e., ai > min_d
                for ai in range(bi):
                    a = ordering[ai]
                    if graph[a][c] and not graph[a][b]:
                        if ai <= min_d:
                            return False
    return True


def _recompute(graph):
    """Recompute the LexBFS ordering from scratch."""
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    return _recompute(graph)


def insert_edge(graph, edge, state):
    """Handle edge insertion. Try to keep the current ordering if still valid."""
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    """Handle edge deletion. Try to keep the current ordering if still valid."""
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    return _recompute(graph)
