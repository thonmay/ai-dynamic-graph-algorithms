"""Dynamic LexBFS ordering (candidate gen001_c03).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge: adding an edge can only make the ordering MORE constrained.
  We check the (LB) 4-point property; if it still holds, the ordering is
  still a valid LexBFS and we keep it (no recompute).  Otherwise we
  recompute from scratch.
- delete_edge: removing an edge can only make the ordering LESS constrained,
  so the 4-point property can be violated.  We check it; if it still holds
  we keep the ordering, otherwise we recompute.

The 4-point check is O(n^3) in the worst case but is usually much cheaper
than a full recompute on sparse graphs, and it avoids recomputation in the
common case where the update does not break the ordering.
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
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

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

    # For each b (position pb), precompute D_b = {d : pos[d] < pb, d adj b}
    # For each a (position pa < pb, a not adj b), precompute C_a = {c : pos[c] > pb, a adj c}
    # For each c in C_a, check if exists d in D_b with pos[d] < pa and d not adj c.

    for pb in range(n):
        b = ordering[pb]
        # D_b: list of (pos, vertex) for d with pos[d] < pb and d adj b
        D_b = []
        for pd in range(pb):
            d = ordering[pd]
            if d in adj[b]:
                D_b.append((pd, d))

        for pa in range(pb):
            a = ordering[pa]
            if a in adj[b]:
                continue  # a adj b, skip
            # a not adj b. Check all c with pc > pb and a adj c.
            for pc in range(pb + 1, n):
                c = ordering[pc]
                if c not in adj[a]:
                    continue  # a not adj c, skip
                # a adj c, a not adj b, pa < pb < pc.
                # Need: exists d in D_b with pos[d] < pa and d not adj c.
                found = False
                for pd, d in D_b:
                    if pd < pa and d not in adj[c]:
                        found = True
                        break
                if not found:
                    return False
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
