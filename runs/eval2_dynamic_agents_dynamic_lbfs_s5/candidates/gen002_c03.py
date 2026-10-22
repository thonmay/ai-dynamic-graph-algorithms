"""Dynamic LexBFS ordering (candidate gen002_c03).

Strategy: maintain a valid LexBFS ordering under single edge flips.

Correctness core:
  * init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
    with a deterministic tie-break (smallest vertex id first).
  * insert_edge: adding an edge can create a NEW 4-point violation (the new
    edge (a,c) can trigger the antecedent "ac in E and ab not in E" for a
    triple that was previously vacuously satisfied).  So we verify the (LB)
    property in O(n^2) using the current ordering; if it still holds we keep
    the ordering, otherwise we recompute.
  * delete_edge: removing an edge can break the 4-point property, so we
    verify the (LB) property in O(n^2) using the current ordering; if it
    still holds we keep the ordering, otherwise we recompute.

The state carries the ordering.  All work is done in pure Python with lists.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list.

    Correct HMPV algorithm:
      * P is an ordered list of buckets; each bucket holds a set of vertices
        that share the same label (frozenset of already-output neighbors).
      * At each step pick the FIRST non-empty bucket in list order, take its
        smallest vertex v, output it, then refine every bucket by adjacency
        to v: the sub-bucket of neighbors of v is moved to the FRONT of P
        (before the original bucket), the non-neighbors stay in place.
      * The label of a vertex is the set of its neighbors among the output
        vertices; the bucket order is the lexicographic order of labels.
    """
    n = len(graph)
    if n == 0:
        return []
    # buckets: ordered list of sets; all vertices start in one bucket.
    buckets = [set(range(n))]
    order = []
    remaining = n

    while remaining:
        # find first non-empty bucket
        idx = None
        for i, bset in enumerate(buckets):
            if bset:
                idx = i
                break
        if idx is None:
            break
        v = min(buckets[idx])
        order.append(v)
        remaining -= 1
        buckets[idx].discard(v)
        # refine: for each bucket, split by adjacency to v.
        # The neighbor sub-bucket goes to the FRONT of the whole list
        # (i.e., before the original bucket's position).
        new_buckets = []
        front = []
        for i, bset in enumerate(buckets):
            if not bset:
                continue
            adj = set()
            nonadj = set()
            for x in bset:
                if graph[x][v]:
                    adj.add(x)
                else:
                    nonadj.add(x)
            if i == idx:
                if adj:
                    new_buckets.append(adj)
                if nonadj:
                    new_buckets.append(nonadj)
            else:
                if nonadj:
                    new_buckets.append(nonadj)
                if adj:
                    front.append(adj)
        buckets = front + new_buckets
    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property: for all a < b < c (positions) with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.
    Returns True if valid."""
    n = len(order)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > b with ac in E
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                # need d < a (position) with db in E and dc not in E
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _canonical_check(graph, order):
    """Check whether `order` equals the deterministic LexBFS of `graph`.
    If yes, no recompute needed.  We do a quick check: re-run lexbfs and
    compare.  This is O(n+m) but only called on insertions."""
    return _lexbfs(graph) == order


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {
        'ordering': order,
        'n': n,
    }


def insert_edge(graph, edge, state):
    order = state['ordering']
    # Adding an edge can create a NEW 4-point violation: the new edge (a,c)
    # can trigger the antecedent "ac in E and ab not in E" for a triple that
    # was previously vacuously satisfied (ac not in E).  So we must verify
    # the (LB) property in O(n^2); if it still holds we keep the ordering,
    # otherwise we recompute.
    if _is_valid_lexbfs(graph, order):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }


def delete_edge(graph, edge, state):
    order = state['ordering']
    # Removing an edge can break the 4-point property.
    # Verify in O(n^2); if still valid, keep; else recompute.
    if _is_valid_lexbfs(graph, order):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }
