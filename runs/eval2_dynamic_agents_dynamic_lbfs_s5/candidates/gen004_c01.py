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

    Buckets are kept in a FIFO queue. When processing the current bucket B,
    its first vertex v is output, and the rest of B is split into B1
    (neighbors of v) and B2 (non-neighbors of v). The split sub-buckets are
    appended to the END of the queue (breadth-first refinement), which is
    what yields the lexicographic property.
    """
    buckets = [list(range(n))]
    i = 0
    order = []
    while i < len(buckets):
        B = buckets[i]
        i += 1
        if not B:
            continue
        v = B[0]
        order.append(v)
        rest = B[1:]
        if not rest:
            continue
        B1 = []
        B2 = []
        for x in rest:
            if adj[v][x]:
                B1.append(x)
            else:
                B2.append(x)
        if B1:
            buckets.append(B1)
        if B2:
            buckets.append(B2)
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
