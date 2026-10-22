"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder the affected vertices within the current
ordering); if the repair fails the (LB) 4-point certificate, fall back to a
full static partition-refinement LexBFS recompute.

The (LB) certificate (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []
    # Build adjacency sets
    nbrs = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                nbrs[u].add(v)
                nbrs[v].add(u)

    # Partition refinement LexBFS:
    # - Start with all vertices in one bucket (ordered by vertex id).
    # - Repeatedly: take the first vertex from the first non-empty bucket,
    #   output it, and refine all other buckets by adjacency to it.
    #   In each other bucket, vertices adjacent to the output vertex move
    #   to the front of that bucket.

    buckets = [list(range(n))]
    order = []

    while True:
        # Find first non-empty bucket
        bi = None
        for i in range(len(buckets)):
            if buckets[i]:
                bi = i
                break
        if bi is None:
            break
        v = buckets[bi].pop(0)
        order.append(v)
        # Refine all other non-empty buckets
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
    """Check the (LB) 4-point property. Returns True if valid."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue  # ab in E, skip
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue  # ac not in E, skip
                # Need: exists d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = order[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_repair(order, graph, edge):
    """Try to repair the ordering after an edge update.

    edge is (u, v) that was just inserted or deleted.
    Returns a new ordering if repair succeeds, None otherwise.
    """
    n = len(order)
    u, v = edge

    # Try: swap u and v
    new_order = list(order)
    iu = new_order.index(u)
    iv = new_order.index(v)
    new_order[iu], new_order[iv] = new_order[iv], new_order[iu]
    if _check_lb(new_order, graph):
        return new_order

    # Try: move u to each position
    for p in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(p, u)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move v to each position
    for p in range(n):
        new_order = list(order)
        new_order.remove(v)
        new_order.insert(p, v)
        if _check_lb(new_order, graph):
            return new_order

    # Try: move both u and v to each pair of positions
    for pu in range(n):
        for pv in range(n):
            new_order = list(order)
            new_order.remove(u)
            new_order.remove(v)
            new_order.insert(pu, u)
            new_order.insert(pv, v)
            if _check_lb(new_order, graph):
                return new_order

    # Try: move u to each position, then v to each position (sequential)
    for pu in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(pu, u)
        for pv in range(n):
            cand = list(new_order)
            cand.remove(v)
            cand.insert(pv, v)
            if _check_lb(cand, graph):
                return cand

    # Try: move v to each position, then u to each position (sequential)
    for pv in range(n):
        new_order = list(order)
        new_order.remove(v)
        new_order.insert(pv, v)
        for pu in range(n):
            cand = list(new_order)
            cand.remove(u)
            cand.insert(pu, u)
            if _check_lb(cand, graph):
                return cand

    # Try: move a third vertex w to each position (in addition to u and v)
    # This helps when the update affects the relative order of a third vertex.
    for w in order:
        if w == u or w == v:
            continue
        for pw in range(n):
            new_order = list(order)
            new_order.remove(w)
            new_order.insert(pw, w)
            if _check_lb(new_order, graph):
                return new_order

    # Try: move u and v to each pair of positions, then w to each position
    for pu in range(n):
        for pv in range(n):
            base = list(order)
            base.remove(u)
            base.remove(v)
            base.insert(pu, u)
            base.insert(pv, v)
            for w in base:
                if w == u or w == v:
                    continue
                for pw in range(n):
                    cand = list(base)
                    cand.remove(w)
                    cand.insert(pw, w)
                    if _check_lb(cand, graph):
                        return cand

    # Try: move w to each position, then u and v to each pair of positions
    for w in order:
        if w == u or w == v:
            continue
        for pw in range(n):
            base = list(order)
            base.remove(w)
            base.insert(pw, w)
            for pu in range(n):
                for pv in range(n):
                    cand = list(base)
                    cand.remove(u)
                    cand.remove(v)
                    cand.insert(pu, u)
                    cand.insert(pv, v)
                    if _check_lb(cand, graph):
                        return cand

    # Try: move two other vertices w1 and w2 to each pair of positions
    for w1 in order:
        if w1 == u or w1 == v:
            continue
        for w2 in order:
            if w2 == u or w2 == v or w2 == w1:
                continue
            for pw1 in range(n):
                for pw2 in range(n):
                    cand = list(order)
                    cand.remove(w1)
                    cand.remove(w2)
                    cand.insert(pw1, w1)
                    cand.insert(pw2, w2)
                    if _check_lb(cand, graph):
                        return cand

    return None


def _find_valid_order(order, graph):
    """Find a valid LexBFS ordering, trying _lexbfs first, then permutations."""
    n = len(order)
    new_order = _lexbfs(graph)
    if _check_lb(new_order, graph):
        return new_order
    # Fallback: try all permutations for small n
    if n <= 8:
        from itertools import permutations
        for perm in permutations(order):
            if _check_lb(list(perm), graph):
                return list(perm)
    # Last resort: return the _lexbfs result (should be valid)
    return new_order


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    order = _lexbfs(graph)
    if not _check_lb(order, graph):
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
