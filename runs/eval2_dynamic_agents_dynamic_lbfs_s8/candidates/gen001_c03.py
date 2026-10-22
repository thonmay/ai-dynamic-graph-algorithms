"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each edge update, first try a
cheap local repair (reorder only the affected region); if the repair cannot
prove validity, fall back to a full O(n^2) partition-refinement LexBFS.

The (LB) 4-point property (Corneil & Krueger) certifies validity:
  for all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.
"""


def _lexbfs_full(graph):
    """Static partition-refinement LexBFS, O(n^2) with adjacency matrix."""
    n = len(graph)
    if n == 0:
        return []
    # buckets: list of (label, [vertices]); label = frozenset of vertices
    # that have split this bucket.
    buckets = [(frozenset(), list(range(n)))]
    order = []
    for _ in range(n):
        bi = 0
        while bi < len(buckets) and not buckets[bi][1]:
            bi += 1
        if bi == len(buckets):
            break
        label, verts = buckets[bi]
        v = verts.pop(0)
        order.append(v)
        new_buckets = []
        for lab, vs in buckets:
            if not vs:
                continue
            neigh = [x for x in vs if graph[v][x]]
            non = [x for x in vs if not graph[v][x]]
            if neigh:
                new_buckets.append((lab | frozenset([v]), neigh))
            if non:
                new_buckets.append((lab, non))
        buckets = new_buckets
    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property.

    For each non-edge (a, b) with a before b, every c after b that is
    adjacent to a must be "covered": there must exist d before a with
    db in E and dc not in E.

    Optimized: for a fixed (a, b), precompute the set of d's before a
    that are adjacent to b.  Then for each c > b with ac in E, check
    whether any such d is non-adjacent to c.
    """
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue
            # Collect d's before a that are adjacent to b.
            d_list = []
            for t in range(i):
                d = order[t]
                if graph[d][b]:
                    d_list.append(d)
            if not d_list:
                # No d covers anything; any c > b with ac in E is a violation.
                for k in range(j + 1, n):
                    if graph[a][order[k]]:
                        return False
                continue
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                found = False
                for d in d_list:
                    if not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_local_repair(graph, order, edge, state):
    """Attempt a cheap local repair after an edge update.

    Returns a new ordering if it can be proven valid, else None.
    """
    u, v = edge
    pos = state.get('pos')
    if pos is None:
        return None
    pu, pv = pos[u], pos[v]
    if pu > pv:
        u, v = v, u
        pu, pv = pv, pu
    lo, hi = pu, pv
    segment = order[lo:hi + 1]
    if len(segment) <= 2:
        return order  # nothing to reorder
    sub = segment
    m = len(sub)
    # Run LexBFS on the induced subgraph, forcing the first vertex to be
    # segment[0] (keep the prefix stable).
    buckets = [(frozenset(), list(range(m)))]
    sub_order = []
    for _ in range(m):
        bi = 0
        while bi < len(buckets) and not buckets[bi][1]:
            bi += 1
        if bi == len(buckets):
            break
        label, verts = buckets[bi]
        if not sub_order:
            # force vertex 0 first
            if 0 in verts:
                verts.remove(0)
            else:
                found = False
                for lab2, vs2 in buckets:
                    if 0 in vs2:
                        vs2.remove(0)
                        found = True
                        break
                if not found:
                    return None
            v0 = 0
        else:
            v0 = verts.pop(0)
        sub_order.append(v0)
        new_buckets = []
        for lab, vs in buckets:
            if not vs:
                continue
            neigh = [x for x in vs if graph[sub[v0]][sub[x]]]
            non = [x for x in vs if not graph[sub[v0]][sub[x]]]
            if neigh:
                new_buckets.append((lab | frozenset([v0]), neigh))
            if non:
                new_buckets.append((lab, non))
        buckets = new_buckets
    if len(sub_order) != m:
        return None
    new_segment = [sub[i] for i in sub_order]
    new_order = order[:lo] + new_segment + order[hi + 1:]
    if _is_valid_lexbfs(graph, new_order):
        return new_order
    return None


def _make_state(graph, order):
    pos = [0] * len(order)
    for i, v in enumerate(order):
        pos[v] = i
    return {'ordering': order, 'pos': pos}


def init(graph):
    order = _lexbfs_full(graph)
    return _make_state(graph, order)


def insert_edge(graph, edge, state):
    order = state['ordering']
    new_order = _try_local_repair(graph, order, edge, state)
    if new_order is None:
        new_order = _lexbfs_full(graph)
    # Final safety net: verify, recompute if needed.
    if not _is_valid_lexbfs(graph, new_order):
        new_order = _lexbfs_full(graph)
    return _make_state(graph, new_order)


def delete_edge(graph, edge, state):
    order = state['ordering']
    new_order = _try_local_repair(graph, order, edge, state)
    if new_order is None:
        new_order = _lexbfs_full(graph)
    # Final safety net: verify, recompute if needed.
    if not _is_valid_lexbfs(graph, new_order):
        new_order = _lexbfs_full(graph)
    return _make_state(graph, new_order)
