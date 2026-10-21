"""Dynamic LexBFS ordering (undirected).

Strategy: maintain a valid LexBFS ordering. On each update, verify the
(LB) 4-point property on the new graph; if it fails, recompute from
scratch with the standard partition-refinement LexBFS (O(n+m)).

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Standard partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # adj: for each vertex, set of neighbors
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    ordered = []
    remaining = set(range(n))
    # label[v] = list of 0/1 for each ordered vertex (in order),
    # 0 if adjacent (neighbors sort first), 1 if not adjacent.
    labels = {v: [] for v in range(n)}

    for _ in range(n):
        # Find the vertex in remaining with lexicographically smallest label
        best = None
        best_label = None
        for v in sorted(remaining):
            if best is None or labels[v] < best_label:
                best = v
                best_label = labels[v]
        ordered.append(best)
        remaining.discard(best)
        # Update labels of remaining vertices
        for v in remaining:
            labels[v].append(0 if best in adj[v] else 1)

    return ordered


def _check_lb_full(graph, ordering):
    """Check the (LB) 4-point property. Returns True if ordering is valid LexBFS.

    For each position i (vertex a), precompute:
      - N_a: set of neighbors of a
      - S_a: set of vertices d at position < i that are adjacent to a
    Then for each b at position j > i with ab not in E, the constraint
    "exists d < a with db in E and dc not in E" for c at position k > j
    with ac in E is equivalent to:
      (N_b & S_a) - N_c is non-empty,
    i.e. N_b & S_a is not a subset of N_c.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # Precompute neighbor sets
    N = [set() for _ in range(n)]
    for i in range(n):
        a = ordering[i]
        row = graph[a]
        for j in range(n):
            if row[j]:
                N[i].add(j)

    # S_a: neighbors of a that appear before a in the ordering
    S = [set() for _ in range(n)]
    for i in range(n):
        a = ordering[i]
        for j in range(i):
            if j in N[i]:
                S[i].add(j)

    for i in range(n):
        a = ordering[i]
        S_a = S[i]
        # For each b at position j > i with ab not in E:
        for j in range(i + 1, n):
            b = ordering[j]
            if j in N[i]:
                continue  # ab in E, no constraint
            # ab not in E. Compute N_b & S_a once.
            common = N[j] & S_a
            # For each c at position k > j with ac in E,
            # need common - N_c non-empty.
            for k in range(j + 1, n):
                c = ordering[k]
                if k not in N[i]:
                    continue  # ac not in E, no constraint
                # Need: exists d in common with d not in N[k]
                if common <= N[k]:
                    return False
    return True


def _check_lb_local(graph, ordering, u, v):
    """Check the (LB) 4-point property, but only for triples where the
    deleted/inserted edge (u,v) could affect the witness.

    The edge (u,v) can only affect the check for triples (a, b, c) where:
      - b == u or b == v (the edge (d,b) or (b,c) involves the changed edge)
      - or a == u or a == v (the edge (a,c) involves the changed edge)
      - or c == u or c == v (the edge (a,c) involves the changed edge)

    So we only need to check triples where at least one of a, b, c is u or v.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # Find positions of u and v in the ordering
    pos = {vertex: i for i, vertex in enumerate(ordering)}
    pu = pos[u]
    pv = pos[v]

    # Precompute neighbor sets
    N = [set() for _ in range(n)]
    for i in range(n):
        a = ordering[i]
        row = graph[a]
        for j in range(n):
            if row[j]:
                N[i].add(j)

    # S_a: neighbors of a that appear before a in the ordering
    S = [set() for _ in range(n)]
    for i in range(n):
        a = ordering[i]
        for j in range(i):
            if j in N[i]:
                S[i].add(j)

    # Check only triples where a, b, or c is u or v
    for i in range(n):
        a = ordering[i]
        S_a = S[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if j in N[i]:
                continue  # ab in E, no constraint
            # ab not in E. Compute N_b & S_a once.
            common = N[j] & S_a
            for k in range(j + 1, n):
                c = ordering[k]
                # Only check if at least one of a, b, c is u or v
                if a != u and a != v and b != u and b != v and c != u and c != v:
                    continue
                if k not in N[i]:
                    continue  # ac not in E, no constraint
                # Need: exists d in common with d not in N[k]
                if common <= N[k]:
                    return False
    return True


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    if not _check_lb_local(graph, ordering, u, v):
        state['ordering'] = _lexbfs(graph)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    # Deletion can invalidate the (LB) property: a witness d for some
    # triple may have relied on the deleted edge (d,b). Verify and
    # recompute if the ordering is no longer valid.
    ordering = state['ordering']
    if not _check_lb_local(graph, ordering, u, v):
        state['ordering'] = _lexbfs(graph)
    return state
