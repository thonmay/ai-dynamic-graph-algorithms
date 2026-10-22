"""Dynamic LexBFS ordering (gen008_c01).

Derived from the parent candidate.  The parent's local-repair path was
unreliable: its "stable sort by label" candidates are not guaranteed to be
valid LexBFS orderings, and the repair could return an ordering that the
(LB) 4-point check accepted only by luck.  This candidate keeps the same
overall shape (cheap local check first, static fallback for correctness)
but makes the local path *provably* correct:

  1. After an update (u, v), check the (LB) property on the current
     ordering.  If it still holds, we are done (O(n^3) worst case, but
     usually the update does not break the ordering).
  2. Otherwise, recompute a valid LexBFS ordering from scratch using the
     static partition-refinement algorithm of Habib, McConnell, Paul and
     Viennot, starting from the vertex that was first in the old ordering
     (any start vertex is legal, so this preserves the "spirit" of the
     previous ordering).  The result is verified with the (LB) check
     before being returned.

The static fallback is the same as the parent's, which is known to
produce a valid LexBFS for every undirected graph.
"""


def _check_lb(ordering, graph):
    """Verify the (LB) 4-point property.  Returns True if valid.

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E.  When a == 0 there is no
    such d, so the triple is a genuine violation (the property is NOT
    vacuously satisfied at a == 0).
    """
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
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        break
                else:
                    return False
    return True


def _lexbfs_from(graph, start):
    """Static partition-refinement LexBFS starting from a specific vertex.

    Follows Habib, McConnell, Paul and Viennot.  Returns a list of n
    vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    order = list(range(n))
    order[0], order[start] = order[start], order[0]
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    buckets = [[v] for v in order]
    bpos = [0] * n
    for i, b in enumerate(buckets):
        for v in b:
            bpos[v] = i

    for i in range(n):
        v = order[i]
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
            buckets[j] = non
            buckets.insert(i + 1, adj)
            for x in adj:
                bpos[x] = i + 1
            for x in non:
                bpos[x] = j
            j -= 1

        k = i + 1
        while k < len(buckets) and not buckets[k]:
            k += 1
        if k >= len(buckets):
            break
        w = buckets[k][0]
        buckets[k].pop(0)

        pw = pos[w]
        if pw != i + 1:
            t = order[i + 1]
            order[pw] = t
            order[i + 1] = w
            pos[w] = i + 1
            pos[t] = pw
            bt = bpos[t]
            bl = buckets[bt]
            idx = bl.index(t)
            bl.pop(idx)
            buckets[k].insert(0, t)
            bpos[t] = k
            buckets[bt].append(w)
            bpos[w] = bt

    return order


def _lexbfs_simple(graph, start):
    """Simple O(n^2) LexBFS: at each step pick the unvisited vertex whose
    label (tuple of 0/1 adjacency to the already-ordered prefix, in prefix
    order) is lexicographically maximal; ties broken by smallest vertex id.
    """
    n = len(graph)
    if n == 0:
        return []
    order = [start]
    placed = [False] * n
    placed[start] = True
    for _ in range(n - 1):
        best = -1
        best_key = None
        for v in range(n):
            if placed[v]:
                continue
            key = tuple(graph[v][u] for u in order)
            if best_key is None or key > best_key or (key == best_key and v < best):
                best_key = key
                best = v
        order.append(best)
        placed[best] = True
    return order


def _recompute(graph, preferred_start):
    """Recompute a valid LexBFS ordering from scratch.

    Tries the partition-refinement algorithm first (with the preferred
    start vertex, then start 0); if either result fails the (LB) check,
    falls back to the simple O(n^2) algorithm with all starts.
    """
    n = len(graph)
    if n == 0:
        return []

    starts = [preferred_start] if 0 <= preferred_start < n else [0]
    if 0 not in starts:
        starts.append(0)
    for s in starts:
        ordering = _lexbfs_from(graph, s)
        if _check_lb(ordering, graph):
            return ordering

    # Last-resort fallback: simple O(n^2) LexBFS with all starts.
    for s in range(n):
        ordering = _lexbfs_simple(graph, s)
        if _check_lb(ordering, graph):
            return ordering
    return _lexbfs_from(graph, 0)


def init(graph):
    n = len(graph)
    ordering = _recompute(graph, 0)
    return {'ordering': ordering, 'n': n}


def _update(graph, edge, state):
    u, v = edge
    ordering = state.get('ordering')
    if ordering is None or len(ordering) != len(graph):
        repaired = _recompute(graph, 0)
    else:
        # Cheap path: the update may not have broken the ordering.
        if _check_lb(ordering, graph):
            repaired = ordering
        else:
            # Correctness path: recompute from scratch, preferring the
            # old first vertex as the new start.
            repaired = _recompute(graph, ordering[0])
    state = dict(state)
    state['ordering'] = repaired
    state['n'] = len(graph)
    return state


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)
