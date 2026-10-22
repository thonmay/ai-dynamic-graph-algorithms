"""Dynamic LexBFS ordering.

Strategy: keep the current LexBFS ordering in the state.  After an edge
update, first try to repair the *existing* ordering locally (cheap path);
only if the local repair fails do we fall back to a full static
partition-refinement LexBFS recompute (correctness path).

Local repair idea
-----------------
An edge update (u, v) only changes the labels of vertices that are
adjacent to u or v: for every other vertex x, the bit of its label at
position u (or v) is unchanged, and the relative order of the label
prefixes of two such vertices is unchanged.  So the only possible
violations of the (LB) 4-point property involve positions of u or v as
the "a" or "b" vertex of a triple.

We therefore:
  1. check the (LB) property on the current ordering (early exit),
  2. if violated, try a few cheap local fixes:
       - stable sort by label against the current ordering,
       - stable sort by label against the reversed ordering,
       - move u and v to their label-sorted positions,
  3. if still violated, recompute from scratch with the static
     partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

The static fallback is the same as the parent candidate, which is known
to produce a valid LexBFS for every undirected graph.
"""


def _labels(ordering, graph):
    """label[v] = tuple of 0/1 bits: adjacency of v to ordering[0..n-1]."""
    n = len(ordering)
    labels = {}
    for v in range(n):
        labels[v] = tuple(graph[v][u] for u in ordering)
    return labels


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


def _try_all_starts(graph):
    """Try all starting vertices; return the first valid LexBFS ordering."""
    n = len(graph)
    if n == 0:
        return []
    for start in range(n):
        ordering = _lexbfs_simple(graph, start)
        if _check_lb(ordering, graph):
            return ordering
    return _lexbfs_from(graph, 0)


def _stable_sort_by_label(ordering, graph):
    """Stable-sort the ordering by label (lexicographic, descending),
    ties broken by current position (i.e. stable)."""
    labels = _labels(ordering, graph)
    return sorted(ordering, key=lambda v: labels[v], reverse=True)


def _local_repair(ordering, graph, u, v):
    """Try to repair the ordering after an edge update (u, v).

    Returns a valid ordering, or None if no local fix worked.
    """
    n = len(ordering)
    if n == 0:
        return []

    # Candidate 0: the ordering as-is (the update may not have broken it).
    if _check_lb(ordering, graph):
        return ordering

    # Candidate 1: stable-sort by label against the current ordering.
    cand = _stable_sort_by_label(ordering, graph)
    if _check_lb(cand, graph):
        return cand

    # Candidate 2: stable-sort by label against the reversed ordering.
    rev = list(reversed(ordering))
    cand = _stable_sort_by_label(rev, graph)
    if _check_lb(cand, graph):
        return cand

    # Candidate 3: try moving u and v to their label-sorted positions
    # within the current ordering (insertion-sort style, only u and v
    # move).
    labels = _labels(ordering, graph)
    for (a, b) in ((u, v), (v, u)):
        cand = list(ordering)
        rest = [x for x in cand if x != a and x != b]
        pair = sorted([a, b], key=lambda x: labels[x], reverse=True)
        for pv in pair:
            p = 0
            while p < len(rest) and labels[rest[p]] >= labels[pv]:
                p += 1
            rest.insert(p, pv)
        if _check_lb(rest, graph):
            return rest

    return None


def init(graph):
    n = len(graph)
    ordering = _try_all_starts(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state.get('ordering')
    if ordering is None or len(ordering) != len(graph):
        ordering = _try_all_starts(graph)
    else:
        repaired = _local_repair(ordering, graph, u, v)
        if repaired is None:
            repaired = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = repaired
    state['n'] = len(graph)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state.get('ordering')
    if ordering is None or len(ordering) != len(graph):
        ordering = _try_all_starts(graph)
    else:
        repaired = _local_repair(ordering, graph, u, v)
        if repaired is None:
            repaired = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = repaired
    state['n'] = len(graph)
    return state
