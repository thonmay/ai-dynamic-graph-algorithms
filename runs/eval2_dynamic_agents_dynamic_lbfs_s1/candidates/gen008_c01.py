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

    Efficient O(n^3) implementation:
    For each pair (b, c) with pos[b] < pos[c], we need to verify that for
    every a with pos[a] < pos[b], graph[a][c]=1, graph[a][b]=0, there exists
    d with pos[d] < pos[a], graph[d][b]=1, graph[d][c]=0.

    Key insight: for fixed (b, c), define
      good_d = {d : pos[d] < pos[b], graph[d][b]=1, graph[d][c]=0}
    Then the condition for a given a is: min(good_d) < pos[a].
    So we just need min(good_d) and the max pos[a] among violating a's.
    """
    n = len(ordering)
    if n <= 2:
        return True

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
            # Find max position a < bi with graph[ordering[a]][c]=1 and graph[ordering[a]][b]=0
            max_a = -1
            for ai in range(bi - 1, -1, -1):
                a = ordering[ai]
                if graph[a][c] and not graph[a][b]:
                    max_a = ai
                    break
            if max_a >= 0 and min_d > max_a:
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
