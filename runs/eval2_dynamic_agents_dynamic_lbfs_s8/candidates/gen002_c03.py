"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder the affected vertices within the current
ordering); if the repair fails the (LB) 4-point certificate, fall back to a
full static partition-refinement LexBFS recompute.

The (LB) certificate (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.

Optimizations over the parent:
- _check_lb_fast: O(n^3) certificate check using bitmasks (vs O(n^4)).
- _try_repair: only tries moves of the two affected vertices (u, v).
- _find_valid_order: tries _lexbfs first, then a seeded recompute.
"""


def _lexbfs(graph, start=None):
    """Static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

    Returns a list of all n vertices in a valid LexBFS order.
    If start is given, the first vertex output is `start`.
    """
    n = len(graph)
    if n == 0:
        return []
    nbrs = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                nbrs[u].add(v)
                nbrs[v].add(u)

    if start is not None:
        buckets = [[start] + [x for x in range(n) if x != start]]
    else:
        buckets = [list(range(n))]

    order = []

    while True:
        bi = None
        for i in range(len(buckets)):
            if buckets[i]:
                bi = i
                break
        if bi is None:
            break
        v = buckets[bi].pop(0)
        order.append(v)
        for j in range(len(buckets)):
            if j == bi or not buckets[j]:
                continue
            adj = []
            not_adj = []
            for x in buckets[j]:
                if x in nbrs[v]:
                    adj.append(x)
                else:
                    not_adj.append(x)
            buckets[j] = adj + not_adj
        if not buckets[bi]:
            del buckets[bi]

    return order


def _check_lb(order, graph):
    """Check the (LB) 4-point property. Returns True if valid. O(n^4)."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue
                found = False
                for d in range(a):
                    vd = order[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _check_lb_fast(order, graph):
    """Fast O(n^3) check of the (LB) 4-point property using bitmasks.

    For each (a, c) with a < c and ac in E, compute:
      cover = union of N(order[d]) for d < a with order[d] not~ order[c]
    Then for each b in (a, c) with ab not in E, check vb in cover.
    """
    n = len(order)
    if n <= 1:
        return True

    nbr_mask = [0] * n
    for u in range(n):
        row = graph[u]
        m = 0
        for v in range(n):
            if row[v]:
                m |= (1 << v)
        nbr_mask[u] = m

    for a in range(n):
        va = order[a]
        na = nbr_mask[va]
        for c in range(a + 2, n):
            vc = order[c]
            if not (na >> vc) & 1:
                continue
            cover = 0
            for d in range(a):
                vd = order[d]
                if not (nbr_mask[vd] >> vc) & 1:
                    cover |= nbr_mask[vd]
            for b in range(a + 1, c):
                vb = order[b]
                if (na >> vb) & 1:
                    continue
                if not (cover >> vb) & 1:
                    return False
    return True


def _try_repair(order, graph, edge):
    """Try to repair the ordering after an edge update.

    edge is (u, v) that was just inserted or deleted.
    Returns a new ordering if repair succeeds, None otherwise.
    """
    n = len(order)
    u, v = edge

    new_order = list(order)
    iu = new_order.index(u)
    iv = new_order.index(v)
    new_order[iu], new_order[iv] = new_order[iv], new_order[iu]
    if _check_lb_fast(new_order, graph):
        return new_order

    for p in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(p, u)
        if _check_lb_fast(new_order, graph):
            return new_order

    for p in range(n):
        new_order = list(order)
        new_order.remove(v)
        new_order.insert(p, v)
        if _check_lb_fast(new_order, graph):
            return new_order

    return None


def _find_valid_order(order, graph):
    """Find a valid LexBFS ordering, trying _lexbfs first, then seeded variants."""
    n = len(order)
    new_order = _lexbfs(graph)
    if _check_lb_fast(new_order, graph):
        return new_order
    if n > 0:
        new_order2 = _lexbfs(graph, start=order[0])
        if _check_lb_fast(new_order2, graph):
            return new_order2
    if n <= 8:
        from itertools import permutations
        for perm in permutations(order):
            if _check_lb_fast(list(perm), graph):
                return list(perm)
    return new_order


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    order = _lexbfs(graph)
    if not _check_lb_fast(order, graph):
        order = _find_valid_order(order, graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    """Handle edge insertion. Return new state."""
    order = state['ordering']
    new_order = _try_repair(order, graph, edge)
    if new_order is not None:
        return {'ordering': new_order}
    new_order = _find_valid_order(order, graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    """Handle edge deletion. Return new state."""
    order = state['ordering']
    new_order = _try_repair(order, graph, edge)
    if new_order is not None:
        return {'ordering': new_order}
    new_order = _find_valid_order(order, graph)
    return {'ordering': new_order}
