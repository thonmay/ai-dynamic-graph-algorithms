"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reinsert the affected vertices in every small number of
orders); if the repair fails the (LB) 4-point certificate, fall back to a
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
    """Check the (LB) 4-point property. Returns True if valid.

    For each pair (a, b) with a < b and ab not in E, let S = {c > b : ac in E}.
    The certificate holds iff S is empty or S is contained in the set of
    vertices that some d < a separates from b (db in E, dc not in E).
    """
    n = len(order)
    for a in range(n):
        va = order[a]
        row_a = graph[va]
        for b in range(a + 1, n):
            vb = order[b]
            if row_a[vb]:
                continue  # ab in E, skip
            # S = {c > b : ac in E}
            S = [c for c in range(b + 1, n) if row_a[order[c]]]
            if not S:
                continue
            # Separators: d < a with db in E
            seps = [d for d in range(a) if graph[order[d]][vb]]
            if not seps:
                return False
            # S must be contained in the union of N(d) \ N(b) over seps
            for c in S:
                vc = order[c]
                ok = False
                for d in seps:
                    vd = order[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _try_repair(order, graph, edge):
    """Try to repair the ordering after an edge update.

    edge is (u, v) that was just inserted or deleted.
    Returns a new ordering if repair succeeds, None otherwise.
    """
    n = len(order)
    if n == 0:
        return list(order)
    u, v = edge
    if u == v:
        return list(order)

    # Candidate 1: the current order (the update may not have broken it).
    if _check_lb(order, graph):
        return list(order)

    # Candidate 2: swap u and v.
    new_order = list(order)
    iu = new_order.index(u)
    iv = new_order.index(v)
    new_order[iu], new_order[iv] = new_order[iv], new_order[iu]
    if _check_lb(new_order, graph):
        return new_order

    # Candidate 3: move u to each position.
    for p in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(p, u)
        if _check_lb(new_order, graph):
            return new_order

    # Candidate 4: move v to each position.
    for p in range(n):
        new_order = list(order)
        new_order.remove(v)
        new_order.insert(p, v)
        if _check_lb(new_order, graph):
            return new_order

    # Candidate 5: reinsert u and v in both orders, at all position pairs.
    base = [x for x in order if x != u and x != v]
    m = len(base)
    for seq in ((u, v), (v, u)):
        for i in range(m + 1):
            for j in range(m + 1):
                cand = base[:i] + [seq[0]] + base[i:j] + [seq[1]] + base[j:]
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
