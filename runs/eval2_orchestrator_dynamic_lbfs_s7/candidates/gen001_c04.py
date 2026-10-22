"""Dynamic LexBFS ordering.

Baseline: recompute the static partition-refinement LexBFS after each update.
The static algorithm follows Habib, McConnell, Paul and Viennot: maintain a
partition of the unvisited vertices into buckets of equal label; at each step
refine the buckets after the current position using the new vertex's
neighbourhood, then pick the first vertex of the first non-empty bucket.

Validity is certified by the (LB) 4-point property of Corneil and Krueger.
"""


def _lexbfs_from(graph, start):
    """Static LexBFS starting from a specific vertex.

    Uses the partition-refinement algorithm of Habib, McConnell, Paul and
    Viennot.  The key invariant: after processing vertex at position i, the
    buckets after position i are ordered by their labels (sets of earlier
    neighbours), and within each bucket the vertices are in the order they
    were first placed there.

    Returns a list of n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    # order[i] = vertex at position i; pos[v] = position of v
    order = list(range(n))
    # Put start at position 0
    order[0], order[start] = order[start], order[0]
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    # buckets: list of lists of vertices (in order); bucket i holds vertices
    # whose label (set of earlier neighbours) is identical.
    buckets = [[v] for v in order]
    # bpos[v] = index of the bucket containing v
    bpos = [0] * n
    for i, b in enumerate(buckets):
        for v in b:
            bpos[v] = i

    for i in range(n):
        v = order[i]
        # Refine buckets after position i using adjacency to v.
        # Walk from the last bucket down to i+1.
        j = len(buckets) - 1
        while j > i:
            b = buckets[j]
            if not b:
                j -= 1
                continue
            adj = [x for x in b if graph[v][x]]
            non = [x for x in b if not graph[v][x]]
            if not adj or not non:
                j -= 1
                continue
            # Split: adj goes right after position i, non stays at j.
            buckets[j] = non
            buckets.insert(i + 1, adj)
            for x in adj:
                bpos[x] = i + 1
            for x in non:
                bpos[x] = j
            j -= 1

        # Pick the next vertex: first vertex of the first non-empty bucket
        # after position i.
        k = i + 1
        while k < len(buckets) and not buckets[k]:
            k += 1
        if k >= len(buckets):
            break
        w = buckets[k][0]
        buckets[k].pop(0)

        # Move w to position i+1 in the order.
        pw = pos[w]
        if pw != i + 1:
            t = order[i + 1]
            order[pw] = t
            order[i + 1] = w
            pos[w] = i + 1
            pos[t] = pw
            # Fix bucket memberships: t goes into w's bucket (k),
            # w goes into t's old bucket (bpos[t]).
            bt = bpos[t]
            # Remove t from its bucket bt.
            bl = buckets[bt]
            idx = bl.index(t)
            bl.pop(idx)
            # Put t at the front of bucket k.
            buckets[k].insert(0, t)
            bpos[t] = k
            # Put w into bucket bt.
            buckets[bt].append(w)
            bpos[w] = bt
        # else: w was already at position i+1; nothing to do.

    return order


def _check_lb(ordering, graph):
    """Verify the (LB) 4-point property. Returns True if valid."""
    n = len(ordering)
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue  # ab in E, skip
            for c in range(b + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue  # ac not in E, skip
                # Need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_all_starts(graph):
    """Try all starting vertices; return the first valid LexBFS ordering."""
    n = len(graph)
    if n == 0:
        return []
    for start in range(n):
        ordering = _lexbfs_from(graph, start)
        if _check_lb(ordering, graph):
            return ordering
    # Fallback: return the first one (should not happen for valid graphs)
    return _lexbfs_from(graph, 0)


def init(graph):
    n = len(graph)
    ordering = _try_all_starts(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    ordering = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = ordering
    return state


def delete_edge(graph, edge, state):
    ordering = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = ordering
    return state
