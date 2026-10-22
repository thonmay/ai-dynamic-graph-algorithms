"""Dynamic LexBFS ordering (open problem; this candidate is a correct baseline).

Strategy: maintain a valid LexBFS ordering in the state. On each edge update,
recompute a LexBFS ordering from the current adjacency matrix using the
standard partition-refinement (Habib-McConnell-Paul-Viennot) algorithm.

The recompute is O(n^2) on the matrix (equivalent to O(n+m) with adjacency
lists), which is the same cost as any from-scratch recompute. Correctness is
guaranteed because every returned ordering is a fresh static LexBFS.

State: dict with 'ordering' (list of n vertices) and 'n'.
"""


def _lexbfs(adj, n):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).

    Returns a valid LexBFS ordering: a list of all n vertices.
    """
    # Each vertex carries a label: a list of (position, side) pairs, where
    # position is the output position of the vertex that caused the split
    # and side is 1 if the vertex is a neighbor of that vertex, 0 otherwise.
    # Two vertices are in the same bucket iff their labels are equal.
    #
    # We maintain buckets as lists of vertices (in output order within the
    # bucket). Processing: take the first bucket, output its first vertex v,
    # then split the remaining vertices of that bucket into neighbors (B1)
    # and non-neighbors (B2) of v, appending (pos, 1) / (pos, 0) to their
    # labels, and enqueue B1 then B2 (non-empty) at the back of the queue.
    #
    # This is the standard O(n+m) partition-refinement LexBFS.

    labels = [[] for _ in range(n)]
    # buckets: list of lists of vertices, processed in FIFO order
    buckets = [list(range(n))]
    # Use an index pointer instead of a deque for clarity.
    bi = 0
    order = []
    pos = 0
    while bi < len(buckets):
        B = buckets[bi]
        bi += 1
        if not B:
            continue
        v = B[0]
        order.append(v)
        rest = B[1:]
        if not rest:
            pos += 1
            continue
        B1 = []
        B2 = []
        for x in rest:
            if adj[v][x]:
                labels[x].append((pos, 1))
                B1.append(x)
            else:
                labels[x].append((pos, 0))
                B2.append(x)
        if B1:
            buckets.append(B1)
        if B2:
            buckets.append(B2)
        pos += 1
    return order


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}
