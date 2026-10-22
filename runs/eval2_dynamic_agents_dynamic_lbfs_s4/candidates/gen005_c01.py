"""Dynamic LexBFS ordering (candidate gen005_c01).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge / delete_edge: after the update, check the (LB) 4-point
  property of Corneil and Krueger on the current ordering.  If it still
  holds, the ordering is still a valid LexBFS and we keep it (no recompute).
  Otherwise we recompute from scratch.

The 4-point check uses the full characterization: for all a<b<c<d with
ac in E, ab not in E, bd in E, cd not in E, the ordering is invalid.
This is O(n^4) worst case but avoids recomputation when the ordering
survives the update.
"""


def _lexbfs(graph):
    """Static partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sorted lists; a vertex is in exactly one bucket
    # order of buckets = order in which they were last refined
    buckets = [list(range(n))]
    bkt_of = [0] * n
    pos_in_bucket = list(range(n))

    order = []
    remaining = n

    while remaining > 0:
        # pick the first non-empty bucket, take its first vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = buckets[bi][0]
        buckets[bi].pop(0)
        pos_in_bucket[v] = -1
        order.append(v)
        remaining -= 1

        # refine every bucket by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = [x for x in b if graph[v][x]]
            nnb = [x for x in b if not graph[v][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets
        for i, b in enumerate(buckets):
            for j, x in enumerate(b):
                bkt_of[x] = i
                pos_in_bucket[x] = j

    return order


def _check_lb_property(graph, ordering):
    """Check the full (LB) 4-point property of Corneil and Krueger.

    The ordering is a valid LexBFS ordering iff for all positions
    a < b < c < d with ac in E, ab not in E, bd in E, cd not in E,
    this configuration never occurs.

    Equivalently: for all a < b < c < d, NOT (ac in E AND ab not in E
    AND bd in E AND cd not in E).

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(ordering)
    if n == 0:
        return True

    # Precompute adjacency as sets for O(1) lookup
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)

    # For each pair (b, d) with b < d and bd in E:
    #   For each a < b with ab not in E:
    #     For each c with b < c < d and ac in E and cd not in E:
    #       -> violation
    #
    # More efficient: iterate over (a, b, c, d) but prune early.
    #
    # Alternative: for each (b, d) with bd in E, precompute:
    #   A_bd = {a < b : ab not in E}
    #   C_bd = {c : b < c < d, cd not in E}
    # Then check if exists a in A_bd and c in C_bd with ac in E.

    for pb in range(n):
        b = ordering[pb]
        for pd in range(pb + 1, n):
            d = ordering[pd]
            if d not in adj[b]:
                continue  # bd not in E, skip
            # bd in E. Now find a < b with ab not in E, and c with b < c < d, cd not in E, ac in E.
            # Precompute C: vertices c at positions (pb+1, pd) with cd not in E
            C = []
            for pc in range(pb + 1, pd):
                c = ordering[pc]
                if c not in adj[d]:
                    C.append(c)
            if not C:
                continue
            # For each a < b with ab not in E, check if a is adjacent to any c in C
            for pa in range(pb):
                a = ordering[pa]
                if a in adj[b]:
                    continue  # ab in E, skip
                # ab not in E. Check if a adj any c in C.
                for c in C:
                    if a in adj[c]:
                        return False  # violation found
    return True


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _check_lb_property(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _check_lb_property(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
