"""Dynamic LexBFS ordering (candidate gen001_c04).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core: after any update, if the previously maintained ordering
is no longer a valid LexBFS ordering, recompute a fresh one with the
standard O(n^2) partition-refinement LexBFS.  If it is still valid, keep
it (no recompute).  Validity is checked with the (LB) 4-point property of
Corneil and Krueger: for all positions a < b < c with ac in E and ab not
in E, there exists d < a with db in E and dc not in E.
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


def _is_valid_lexbfs(order, graph):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(order)
    if n == 0:
        return True

    # Precompute adjacency as sets for O(1) lookup.
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if graph[i][j]:
                adj[i].add(j)
                adj[j].add(i)

    # For each pair (a, b) with a < b in the ordering:
    #   if ab not in E, then for all c > b with ac in E,
    #   there must exist d < a with db in E and dc not in E.
    #
    # Equivalently: for each (a, b) with ab not in E,
    #   the set of c > b with ac in E must NOT be a subset of
    #   the intersection of adj[d] for all d < a with db in E.
    #
    # More directly: for each (a, b) with ab not in E,
    #   let D = {d : pos[d] < pos[a], db in E}
    #   For each c > b with ac in E:
    #     need: exists d in D with dc not in E
    #     i.e., D is not a subset of adj[c]

    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            # Check: is ab in E?
            if b in adj[a]:
                continue  # ab in E, no constraint
            # ab not in E.
            # Precompute D = {d : pos[d] < pos[a], db in E}.
            D = []
            for k in range(i):
                d = order[k]
                if b in adj[d]:
                    D.append(d)

            # Now check all c > b with ac in E.
            for l in range(j + 1, n):
                c = order[l]
                if c not in adj[a]:
                    continue
                # ac in E, ab not in E, a < b < c.
                # Need: exists d in D with dc not in E.
                found = False
                for d in D:
                    if c not in adj[d]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    # Check if the old ordering is still valid.
    if _is_valid_lexbfs(order, graph):
        return state
    # Recompute.
    order = _lexbfs(graph)
    return {'ordering': order, 'n': state['n']}


def delete_edge(graph, edge, state):
    order = state['ordering']
    # Check if the old ordering is still valid.
    if _is_valid_lexbfs(order, graph):
        return state
    # Recompute.
    order = _lexbfs(graph)
    return {'ordering': order, 'n': state['n']}
