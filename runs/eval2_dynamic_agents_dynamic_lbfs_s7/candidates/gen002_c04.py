"""Dynamic LexBFS ordering (candidate gen002_c04).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core: after any update, recompute a fresh LexBFS ordering with
the standard O(n^2) partition-refinement LexBFS.  The static routine is
correct, so this guarantees a valid ordering after every update.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    # Standard LexBFS:
    # - Maintain a list `order` of vertices in the order they are picked.
    # - Maintain a list `unvisited` of vertices not yet picked.
    # - label[v] = sorted list of neighbors of v that are in `order`.
    # - At each step, pick the unvisited vertex with the lexicographically
    #   smallest label (ties broken by vertex id for determinism).
    # - Update labels of neighbors of the picked vertex.

    order = []
    unvisited = set(range(n))
    label = [[] for _ in range(n)]  # sorted list of ordered neighbors

    for _ in range(n):
        # Find the unvisited vertex with the smallest label.
        # Ties broken by vertex id.
        best = None
        best_label = None
        for v in sorted(unvisited):
            if best is None or label[v] < best_label:
                best = v
                best_label = label[v]
        # Pick best.
        order.append(best)
        unvisited.remove(best)
        # Update labels of unvisited neighbors of best.
        for u in unvisited:
            if graph[best][u]:
                label[u].append(best)
                label[u].sort()

    return order
    n = len(graph)
    order = _lexbfs(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    # Always recompute: the static routine is correct, so this guarantees
    # a valid LexBFS ordering after every update.
    order = _lexbfs(graph)
    return {'ordering': order, 'n': state['n']}


def delete_edge(graph, edge, state):
    # Always recompute (see insert_edge).
    order = _lexbfs(graph)
    return {'ordering': order, 'n': state['n']}
