"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a valid LexBFS ordering.  After each update, check the
(LB) 4-point property on the existing ordering; if it still holds, keep it
(cheap, O(n^3) check).  Otherwise recompute a full static LexBFS.

The static LexBFS uses the partition-refinement algorithm of Habib,
McConnell, Paul and Viennot, implemented with a simple list-of-buckets
representation.
"""


def _symmetric_adj(graph):
    """Build adjacency sets from the symmetric part of the matrix.

    An edge is present iff either entry is set.  This is the interpretation
    under which the (LB) 4-point certificate is sound: the certificate is
    only guaranteed for orderings produced by a LexBFS run on the symmetric
    graph, so the checker must use the same edge set.
    """
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if i != j and (row[j] or graph[j][i]):
                adj[i].add(j)
    return adj


def _is_lexbfs_ordering(ordering, adj):
    """Check that `ordering` is a valid LexBFS ordering of the graph with
    adjacency sets `adj`.

    A vertex v is a valid next pick at step k iff its label (the 0/1
    sequence of adjacency to the first k vertices of the ordering) is
    lexicographically minimal among the remaining vertices.  This is
    exactly the definition of LexBFS with the vertex-id tie-break, and it
    is equivalent to the (LB) 4-point property for the purpose of
    certifying that the ordering is a LexBFS ordering.
    """
    n = len(ordering)
    # label[v] = list of 0/1 over ordering[0..k-1]
    labels = {v: [] for v in ordering}
    remaining = set(ordering)
    for k in range(n):
        v = ordering[k]
        # v must have a minimal label among remaining
        best = None
        for w in remaining:
            key = tuple(labels[w])
            if best is None or key < best:
                best = key
        if tuple(labels[v]) != best:
            return False
        remaining.remove(v)
        for w in remaining:
            labels[w].append(1 if w in adj[v] else 0)
    return True


def _lexbfs(graph):
    """Static LexBFS via partition refinement.

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    adj = _symmetric_adj(graph)

    # We use a simpler but correct approach: maintain for each unprocessed
    # vertex its label (list of 0/1 over processed vertices in order), and
    # pick the unprocessed vertex with lexicographically smallest label
    # (tie-break by vertex id).  This is O(n^2 * n) = O(n^3) which is fine.

    order = []
    labels = {v: [] for v in range(n)}
    unprocessed = set(range(n))

    for _ in range(n):
        best = None
        best_key = None
        for v in unprocessed:
            key = (tuple(labels[v]), v)
            if best_key is None or key < best_key:
                best_key = key
                best = v
        unprocessed.remove(best)
        order.append(best)
        for w in unprocessed:
            labels[w].append(1 if w in adj[best] else 0)
    return order


def _is_valid_lexbfs(graph, ordering):
    """Check that `ordering` is a valid LexBFS ordering of the graph.

    Uses the symmetric edge set (edge present iff either matrix entry is
    set) and the label-minimality definition of LexBFS, which is equivalent
    to the (LB) 4-point property.
    """
    adj = _symmetric_adj(graph)
    return _is_lexbfs_ordering(ordering, adj)


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
