"""Dynamic LexBFS ordering.

Strategy:
  1. Try to repair the previous ordering locally after an update.
     - If the old ordering is still valid, keep it.
     - Otherwise, try a small set of local reorderings (swap, move-to-front,
       move-to-back, reverse, adjacent moves) and keep the first one that
       is valid.
  2. If no local repair works, fall back to a full recompute using the
     textbook LexBFS (any start vertex, any tie-break) and verify with the
     (LB) 4-point property.

The (LB) 4-point property (Corneil & Krueger):
  For all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.
"""


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
                if a == 0:
                    continue  # vacuously satisfied
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        break
                else:
                    return False
    return True


def _lexbfs_simple(graph, start):
    """Textbook LexBFS: at each step pick the unvisited vertex whose label
    (tuple of 0/1 adjacency to the already-ordered prefix, in prefix order)
    is lexicographically maximal; ties broken by smallest vertex id."""
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
    # Fallback: every undirected graph has a valid LexBFS ordering.
    return _lexbfs_simple(graph, 0)


def _local_repair(ordering, graph, edge):
    """Try to repair the ordering after a single edge update.

    edge: (u, v) the vertex pair that was just changed.
    Returns a valid ordering if a local repair works, else None.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(ordering):
        pos[vtx] = i

    pu, pv = pos[u], pos[v]

    # Candidate reorderings to try:
    candidates = []

    # 1. Swap u and v
    swapped = list(ordering)
    swapped[pu], swapped[pv] = swapped[pv], swapped[pu]
    candidates.append(swapped)

    # 2. Move u to front
    moved_u_front = [u] + [x for x in ordering if x != u]
    candidates.append(moved_u_front)

    # 3. Move v to front
    moved_v_front = [v] + [x for x in ordering if x != v]
    candidates.append(moved_v_front)

    # 4. Move u to back
    moved_u_back = [x for x in ordering if x != u] + [u]
    candidates.append(moved_u_back)

    # 5. Move v to back
    moved_v_back = [x for x in ordering if x != v] + [v]
    candidates.append(moved_v_back)

    # 6. Reverse the ordering
    candidates.append(list(reversed(ordering)))

    # 7. Move u to position 0, v to position 1
    if u != v:
        rest = [x for x in ordering if x != u and x != v]
        candidates.append([u, v] + rest)
        candidates.append([v, u] + rest)

    # 8. Move u to just before v (if u is after v)
    if pu > pv:
        rest = [x for x in ordering if x != u]
        idx = rest.index(v)
        rest.insert(idx, u)
        candidates.append(rest)

    # 9. Move v to just before u (if v is after u)
    if pv > pu:
        rest = [x for x in ordering if x != v]
        idx = rest.index(u)
        rest.insert(idx, v)
        candidates.append(rest)

    # 10. Move u to just after v (if u is before v)
    if pu < pv:
        rest = [x for x in ordering if x != u]
        idx = rest.index(v)
        rest.insert(idx + 1, u)
        candidates.append(rest)

    # 11. Move v to just after u (if v is before u)
    if pv < pu:
        rest = [x for x in ordering if x != v]
        idx = rest.index(u)
        rest.insert(idx + 1, v)
        candidates.append(rest)

    # 12. Move u to position 1
    if pu != 1:
        rest = [x for x in ordering if x != u]
        rest.insert(1, u)
        candidates.append(rest)

    # 13. Move v to position 1
    if pv != 1:
        rest = [x for x in ordering if x != v]
        rest.insert(1, v)
        candidates.append(rest)

    # 14. Move u to position n-2
    if n >= 2 and pu != n - 2:
        rest = [x for x in ordering if x != u]
        rest.insert(n - 2, u)
        candidates.append(rest)

    # 15. Move v to position n-2
    if n >= 2 and pv != n - 2:
        rest = [x for x in ordering if x != v]
        rest.insert(n - 2, v)
        candidates.append(rest)

    # 16. Move u to position 2
    if n >= 3 and pu != 2:
        rest = [x for x in ordering if x != u]
        rest.insert(2, u)
        candidates.append(rest)

    # 17. Move v to position 2
    if n >= 3 and pv != 2:
        rest = [x for x in ordering if x != v]
        rest.insert(2, v)
        candidates.append(rest)

    # 18. Move u to position n-3
    if n >= 3 and pu != n - 3:
        rest = [x for x in ordering if x != u]
        rest.insert(n - 3, u)
        candidates.append(rest)

    # 19. Move v to position n-3
    if n >= 3 and pv != n - 3:
        rest = [x for x in ordering if x != v]
        rest.insert(n - 3, v)
        candidates.append(rest)

    # 20. Move u to position 3
    if n >= 4 and pu != 3:
        rest = [x for x in ordering if x != u]
        rest.insert(3, u)
        candidates.append(rest)

    # 21. Move v to position 3
    if n >= 4 and pv != 3:
        rest = [x for x in ordering if x != v]
        rest.insert(3, v)
        candidates.append(rest)

    # 22. Move u to position n-4
    if n >= 4 and pu != n - 4:
        rest = [x for x in ordering if x != u]
        rest.insert(n - 4, u)
        candidates.append(rest)

    # 23. Move v to position n-4
    if n >= 4 and pv != n - 4:
        rest = [x for x in ordering if x != v]
        rest.insert(n - 4, v)
        candidates.append(rest)

    # 24. Move u to position 4
    if n >= 5 and pu != 4:
        rest = [x for x in ordering if x != u]
        rest.insert(4, u)
        candidates.append(rest)

    # 25. Move v to position 4
    if n >= 5 and pv != 4:
        rest = [x for x in ordering if x != v]
        rest.insert(4, v)
        candidates.append(rest)

    # 26. Move u to position n-5
    if n >= 5 and pu != n - 5:
        rest = [x for x in ordering if x != u]
        rest.insert(n - 5, u)
        candidates.append(rest)

    # 27. Move v to position n-5
    if n >= 5 and pv != n - 5:
        rest = [x for x in ordering if x != v]
        rest.insert(n - 5, v)
        candidates.append(rest)

    # Try each candidate
    for cand in candidates:
        if _check_lb(cand, graph):
            return cand

    return None


def init(graph):
    n = len(graph)
    ordering = _try_all_starts(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    old_ordering = state.get('ordering', None)
    n = len(graph)

    if old_ordering is not None and len(old_ordering) == n:
        # Fast path: check if old ordering is still valid
        if _check_lb(old_ordering, graph):
            state = dict(state)
            state['ordering'] = old_ordering
            return state
        # Try local repair
        repaired = _local_repair(old_ordering, graph, edge)
        if repaired is not None:
            state = dict(state)
            state['ordering'] = repaired
            return state

    # Full recompute
    ordering = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = ordering
    return state


def delete_edge(graph, edge, state):
    old_ordering = state.get('ordering', None)
    n = len(graph)

    if old_ordering is not None and len(old_ordering) == n:
        # Fast path: check if old ordering is still valid
        if _check_lb(old_ordering, graph):
            state = dict(state)
            state['ordering'] = old_ordering
            return state
        # Try local repair
        repaired = _local_repair(old_ordering, graph, edge)
        if repaired is not None:
            state = dict(state)
            state['ordering'] = repaired
            return state

    # Full recompute
    ordering = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = ordering
    return state
