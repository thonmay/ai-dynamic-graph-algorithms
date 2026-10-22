"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try to repair
the existing ordering locally (cheap); if repair fails, fall back to a
full O(n^2) partition-refinement LexBFS recompute (always correct).

Validity is checked with the (LB) 4-point property:
  for all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.
"""


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property."""
    n = len(order)
    if n == 0:
        return True
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    for pb in range(n):
        b = order[pb]
        for pc in range(pb + 1, n):
            c = order[pc]
            for pa in range(pb):
                a = order[pa]
                if a in adj[b]:
                    continue
                if a not in adj[c]:
                    continue
                found = False
                for pd in range(pa):
                    d = order[pd]
                    if d in adj[b] and d not in adj[c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _lexbfs_recompute(graph):
    """Full LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)

    unvisited = set(range(n))
    order = []
    start = 0
    order.append(start)
    unvisited.remove(start)

    # buckets: list of [label_frozenset, [vertices]]
    # Label = set of visited vertices adjacent to this bucket's members.
    buckets = []
    for v in sorted(unvisited):
        label = frozenset({start}) if v in adj[start] else frozenset()
        found = False
        for b in buckets:
            if b[0] == label:
                b[1].append(v)
                found = True
                break
        if not found:
            buckets.append([label, [v]])

    # Order buckets by label (most-refined first): buckets containing the
    # most recently visited vertex come first, then by earlier vertices.
    def _label_key(b):
        return tuple(1 if x in b[0] else 0 for x in reversed(order))
    buckets.sort(key=_label_key, reverse=True)

    while unvisited:
        # Pick the first non-empty bucket (list is kept in label order,
        # most-refined first)
        idx = -1
        for i, (label, verts) in enumerate(buckets):
            if verts:
                idx = i
                break
        if idx == -1:
            break
        label, verts = buckets[idx]
        v = verts[0]
        verts[0] = verts[-1]
        verts.pop()
        order.append(v)
        unvisited.remove(v)

        # Refine: for each bucket, split into those adjacent to v and not
        new_buckets = []
        for (lbl, verts2) in buckets:
            if not verts2:
                continue
            in_v = []
            not_v = []
            for x in verts2:
                if x in adj[v]:
                    in_v.append(x)
                else:
                    not_v.append(x)
            if in_v:
                new_buckets.append([lbl | frozenset({v}), in_v])
            if not_v:
                new_buckets.append([lbl, not_v])
        # Buckets containing v in their label have the lexicographically
        # maximal label; move them to the front (preserving relative order).
        new_buckets = [b for b in new_buckets if v in b[0]] + \
                      [b for b in new_buckets if v not in b[0]]
        buckets = new_buckets

    return order


def _try_local_fix(graph, order, u, v):
    """Try to fix the ordering by moving u or v. Returns new order or None."""
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    pu, pv = pos[u], pos[v]
    if pu == pv:
        return None

    # Try: swap u and v
    o2 = order[:]
    o2[pu], o2[pv] = o2[pv], o2[pu]
    if _is_valid_lexbfs(graph, o2):
        return o2

    # Try: move v to just before u
    o2 = order[:]
    o2.pop(pv)
    pu2 = pu - 1 if pv < pu else pu
    o2.insert(pu2, v)
    if _is_valid_lexbfs(graph, o2):
        return o2

    # Try: move u to just before v
    o2 = order[:]
    o2.pop(pu)
    pv2 = pv - 1 if pu < pv else pv
    o2.insert(pv2, u)
    if _is_valid_lexbfs(graph, o2):
        return o2

    # Try: move v to just after u
    o2 = order[:]
    o2.pop(pv)
    pu2 = pu - 1 if pv < pu else pu
    o2.insert(pu2 + 1, v)
    if _is_valid_lexbfs(graph, o2):
        return o2

    # Try: move u to just after v
    o2 = order[:]
    o2.pop(pu)
    pv2 = pv - 1 if pu < pv else pv
    o2.insert(pv2 + 1, u)
    if _is_valid_lexbfs(graph, o2):
        return o2

    return None


def init(graph):
    n = len(graph)
    order = _lexbfs_recompute(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    fixed = _try_local_fix(graph, order, u, v)
    if fixed is not None:
        state['ordering'] = fixed
        return state
    state['ordering'] = _lexbfs_recompute(graph)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    if _is_valid_lexbfs(graph, order):
        return state
    fixed = _try_local_fix(graph, order, u, v)
    if fixed is not None:
        state['ordering'] = fixed
        return state
    state['ordering'] = _lexbfs_recompute(graph)
    return state
