"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder the affected vertices within the current
ordering); if the repair fails the (LB) 4-point certificate, fall back to
a full O(n^2) partition-refinement LexBFS recompute.

The (LB) certificate (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _is_lexbfs(order, adj):
    """Check the (LB) 4-point property. O(n^3) worst case, early exit."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb]:
                continue
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if not adj[va][vc]:
                    continue
                # need d < a with db in E and dc not in E
                ok = False
                for d in range(a):
                    vd = order[d]
                    if adj[vd][vb] and not adj[vd][vc]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _lexbfs(adj):
    """Static partition-refinement LexBFS, O(n^2) with bitmasks.

    Labels are keyed by ordering position (position 0 = most significant
    bit), so integer comparison of the bitmasks equals lexicographic
    comparison of the labels.
    """
    n = len(adj)
    if n == 0:
        return []
    # bitmasks of adjacency
    masks = [0] * n
    for u in range(n):
        m = 0
        row = adj[u]
        for v in range(n):
            if row[v]:
                m |= 1 << v
        masks[u] = m

    order = []
    start = 0
    order.append(start)
    # labels: for each vertex, the set of positions of earlier vertices
    # adjacent to it. Position 0 is the most significant bit, so integer
    # comparison of the bitmasks equals lexicographic comparison of the
    # labels (earliest position = most significant).
    labels = [0] * n
    unvisited = (1 << n) - 1
    unvisited &= ~(1 << start)

    while unvisited:
        # find the unvisited vertex with the lexicographically smallest
        # label. Labels are position-keyed bitmasks where position 0 is
        # the most significant bit, so "smallest label" (earliest
        # position = most significant) is the SMALLEST integer.
        # Tie-break by smallest vertex id (arbitrary, allowed).
        best_label = None
        best_v = -1
        u = unvisited
        while u:
            low = u & (-u)
            v = low.bit_length() - 1
            lab = labels[v]
            if best_label is None or lab < best_label or (lab == best_label and v < best_v):
                best_label = lab
                best_v = v
            u &= u - 1
        order.append(best_v)
        unvisited &= ~(1 << best_v)
        # refine: for each unvisited vertex adjacent to best_v, add the
        # position of best_v to its label
        nb = masks[best_v]
        bit = 1 << (len(order) - 1)
        u = unvisited
        while u:
            low = u & (-u)
            v = low.bit_length() - 1
            if nb & low:
                labels[v] |= bit
            u &= u - 1
    return order


def _try_repair(order, adj, edge):
    """Try to fix the ordering by moving the affected vertices.

    Returns a new ordering if it is valid, else None.
    """
    u, v = edge
    candidates = []

    # 1. swap u and v
    o = list(order)
    iu = o.index(u)
    iv = o.index(v)
    o[iu], o[iv] = o[iv], o[iu]
    candidates.append(o)

    # 2. move u right after v
    o = list(order)
    o.remove(u)
    iv = o.index(v)
    o.insert(iv + 1, u)
    candidates.append(o)

    # 3. move v right after u
    o = list(order)
    o.remove(v)
    iu = o.index(u)
    o.insert(iu + 1, v)
    candidates.append(o)

    # 4. move u to the end
    o = list(order)
    o.remove(u)
    o.append(u)
    candidates.append(o)

    # 5. move v to the end
    o = list(order)
    o.remove(v)
    o.append(v)
    candidates.append(o)

    # 6. move u to the front
    o = list(order)
    o.remove(u)
    o.insert(0, u)
    candidates.append(o)

    # 7. move v to the front
    o = list(order)
    o.remove(v)
    o.insert(0, v)
    candidates.append(o)

    for cand in candidates:
        if _is_lexbfs(cand, adj):
            return cand
    return None


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    new_order = _try_repair(order, graph, edge)
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order, 'n': state['n']}


def delete_edge(graph, edge, state):
    order = state['ordering']
    new_order = _try_repair(order, graph, edge)
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order, 'n': state['n']}
