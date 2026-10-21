"""Dynamic LexBFS ordering (candidate gen002_c02).

Strategy: maintain a valid LexBFS ordering under edge updates.

Core idea
---------
A LexBFS ordering is any ordering that satisfies the (LB) 4-point property:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

We maintain the ordering incrementally:

1. On edge insertion (u, v): the new edge can create new violating
   triples (by making a~c newly true) and can destroy existing witnesses
   (by making d~c true where d!~c was required).  We check whether the
   ordering is still valid via a fast O(n^3) certificate check.  If it
   is, we return immediately.  If not, we recompute a fresh LexBFS
   ordering from scratch using the standard partition-refinement
   algorithm.

2. On edge deletion (u, v): the deleted edge may have been the *only*
   witness for some 4-tuple.  We check whether the ordering is still
   valid via a fast O(n^3) certificate check.  If it is, we return
   immediately.  If not, we recompute a fresh LexBFS ordering from
   scratch using the standard partition-refinement algorithm.

State: dict with 'ordering' (list of n vertices) and 'n'.
"""


def _lexbfs(graph):
    """Compute a LexBFS ordering of the undirected graph (adjacency matrix).

    Uses the standard partition-refinement algorithm.  Returns a list of
    n vertices.
    """
    n = len(graph)
    if n == 0:
        return []

    # Standard partition-refinement LexBFS:
    # - Start with one bucket containing all vertices.
    # - Repeatedly take the first vertex v of the first non-empty bucket.
    # - Remove v from its bucket.
    # - Split the remaining vertices of v's bucket: those adjacent to v
    #   go to the front (as a new bucket), those not adjacent stay.
    # - Append v to the ordering.

    buckets = [list(range(n))]
    order = []

    while True:
        # Find the first non-empty bucket and take its first vertex.
        found = False
        for i in range(len(buckets)):
            if buckets[i]:
                v = buckets[i].pop(0)
                found = True
                break
        if not found:
            break

        order.append(v)

        # Split the rest of bucket i into adj and nonadj.
        adj = [w for w in buckets[i] if graph[v][w]]
        nonadj = [w for w in buckets[i] if not graph[v][w]]

        # Replace bucket i with adj + nonadj.
        if adj and nonadj:
            buckets[i] = adj
            buckets.insert(i + 1, nonadj)
        elif adj:
            buckets[i] = adj
        elif nonadj:
            buckets[i] = nonadj
        else:
            buckets[i] = []

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.  Returns True iff ordering is a
    valid LexBFS ordering.

    For all positions a < b < c with ac in E and ab not in E, there
    exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    if n == 0:
        return True

    # pos[v] = position of v in ordering
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    # For each pair (b, c) with pos[b] < pos[c], compute:
    #   min_pos_W[b][c] = min{ pos[d] : d~b and d!~c }, or INF.
    # Then for each (a, b, c) with pos[a] < pos[b] < pos[c], a~c, a!~b:
    #   need min_pos_W[b][c] < pos[a].

    INF = n + 1
    min_pos_W = [[INF] * n for _ in range(n)]

    for d in range(n):
        pd = pos[d]
        for b in range(n):
            if b == d or not graph[d][b]:
                continue
            pb = pos[b]
            for c in range(n):
                if c == d or c == b or graph[d][c]:
                    continue
                pc = pos[c]
                if pc > pb and pd < min_pos_W[b][c]:
                    min_pos_W[b][c] = pd

    # Check: for each (a, b, c) with pos[a] < pos[b] < pos[c],
    # a~c, a!~b: need min_pos_W[b][c] < pos[a].
    for a in range(n):
        pa = pos[a]
        for b in range(n):
            if b == a or graph[a][b]:
                continue
            pb = pos[b]
            if pb <= pa:
                continue
            for c in range(n):
                if c == a or c == b or not graph[a][c]:
                    continue
                pc = pos[c]
                if pc <= pb:
                    continue
                # a~c, a!~b, pos[a] < pos[b] < pos[c]
                if min_pos_W[b][c] >= pa:
                    return False
    return True


def init(graph):
    """Initialize the state with a LexBFS ordering of the graph."""
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    """Handle edge insertion.  The new edge can create new violating
    triples and destroy existing witnesses, so we must verify the
    ordering against the current graph.  Recompute if invalid."""
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': state['n']}


def delete_edge(graph, edge, state):
    """Handle edge deletion.  Check if the ordering is still valid;
    if not, recompute."""
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'n': state['n']}
