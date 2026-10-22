"""Dynamic LexBFS ordering (candidate gen004_c04).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core: after any update, if the previously maintained ordering
is no longer a valid LexBFS ordering, recompute a fresh one with the
standard O(n^2) partition-refinement LexBFS.  If it is still valid, keep
it (no recompute).  Validity is checked with the (LB) 4-point property of
Corneil and Krueger: for all positions a < b < c with ab in E and ac not
in E, there exists d < a with db not in E and dc in E.
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

    # Standard bucket-based LexBFS (Habib-McConnell-Paul-Viennot).
    #
    # `order` is the list of vertices in the order they are picked.
    # `buckets` is a list of lists; buckets[i] holds the unvisited vertices
    # whose label (the list of already-picked neighbors, in pick order) is
    # exactly order[:i].  The invariant is that buckets are ordered by
    # lexicographic label, so the first non-empty bucket always contains the
    # unvisited vertices with the lexicographically smallest label.
    #
    # When vertex v is picked, every unvisited neighbor u of v moves from
    # buckets[i] to buckets[i+1] (its label gains v at position i).  This is
    # done by scanning each bucket once and splitting it into "neighbors of
    # v" (moved) and "non-neighbors" (staying), which preserves the
    # invariant.

    order = []
    buckets = [list(range(n))]

    for _ in range(n):
        # Find the first non-empty bucket and pick its first vertex.
        i = 0
        while not buckets[i]:
            i += 1
        v = buckets[i].pop(0)
        order.append(v)

        # Split each bucket: neighbors of v move one bucket to the right.
        for k in range(i, len(buckets)):
            if not buckets[k]:
                continue
            stay = []
            move = []
            for u in buckets[k]:
                if graph[v][u]:
                    move.append(u)
                else:
                    stay.append(u)
            buckets[k] = stay
            if move:
                if k + 1 < len(buckets):
                    buckets[k + 1] = move + buckets[k + 1]
                else:
                    buckets.append(move)

    return order


def _is_valid_lexbfs(order, graph):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ab in E and ac not in E,
    there exists d < a with db not in E and dc in E.

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
    #   if ab in E, then for all c > b with ac not in E,
    #   there must exist d < a with db not in E and dc in E.
    #
    # Equivalently: for each (a, b) with ab in E,
    #   let D = {d : pos[d] < pos[a], db not in E}
    #   For each c > b with ac not in E:
    #     need: exists d in D with dc in E
    #     i.e., D is not disjoint from adj[c]

    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            # Check: is ab in E?
            if b not in adj[a]:
                continue  # ab not in E, no constraint
            # ab in E.
            # Precompute D = {d : pos[d] < pos[a], db not in E}.
            D = []
            for k in range(i):
                d = order[k]
                if b not in adj[d]:
                    D.append(d)

            # Now check all c > b with ac not in E.
            for l in range(j + 1, n):
                c = order[l]
                if c in adj[a]:
                    continue
                # ac not in E, ab in E, a < b < c.
                # Need: exists d in D with dc in E.
                found = False
                for d in D:
                    if c in adj[d]:
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
