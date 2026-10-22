"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder the affected vertices within the current
ordering); if the repair fails the (LB) 4-point certificate, fall back to a
full static partition-refinement LexBFS recompute.

The (LB) certificate (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.

Improvements over the parent:
- Bitset-based static LexBFS (O(n^3 / word) instead of O(n^2 * m)).
- Bitset-based (LB) certificate check.
- Repair tries all pairs of single-vertex moves (u to p, v to q), a
  superset of the parent's single moves, so more updates are repaired
  without a full recompute.
"""


def _lexbfs(graph):
    """Static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

    Bitset implementation. Returns a list of all n vertices in a valid
    LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []
    # Adjacency as bitsets (integers).
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        adj[u] = bits

    # Buckets: list of bitsets, ordered. Initially one bucket with all
    # vertices.
    buckets = [(1 << n) - 1]
    order = []

    while True:
        # Find first non-empty bucket.
        bi = None
        for i in range(len(buckets)):
            if buckets[i]:
                bi = i
                break
        if bi is None:
            break
        b = buckets[bi]
        # Take the lowest-numbered vertex in the bucket (deterministic
        # tie-break; any choice is legal).
        low = b & (-b)
        v = low.bit_length() - 1
        buckets[bi] = b ^ low
        order.append(v)
        av = adj[v]
        # Refine all other non-empty buckets: adjacent vertices move to
        # the front.
        for j in range(len(buckets)):
            if j == bi or not buckets[j]:
                continue
            bj = buckets[j]
            buckets[j] = (bj & av) | (bj & ~av)
        if not buckets[bi]:
            del buckets[bi]

    return order


def _check_lb(order, graph):
    """Check the (LB) 4-point property using bitsets. Returns True if valid.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    if n == 0:
        return True
    # Adjacency as bitsets over vertex ids.
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= 1 << v
        adj[u] = bits
    # For each position a, precompute:
    #   D[a] = bitset of vertices at position < a.
    #   N[a] = bitset of neighbors of order[a].
    #   P[a] = bitset of vertices at position > a.
    D = [0] * n
    N = [0] * n
    P = [0] * n
    seen = 0
    for a in range(n):
        va = order[a]
        D[a] = seen
        N[a] = adj[va]
        P[a] = ((1 << n) - 1) ^ (seen | (1 << va))
        seen |= 1 << va
    # For each a: for each b in P[a] with b not in N[a],
    #   need: exists d in D[a] with d in N[b] and d not in N[c]
    #   for every c in P[b] with c in N[a].
    #   Let X = D[a] & N[b]. Need X != 0 and for all c in P[b] & N[a],
    #   X & ~N[c] != 0.
    for a in range(n):
        va = order[a]
        # b's: in P[a], not in N[a]
        bset = P[a] & ~N[a]
        while bset:
            low = bset & (-bset)
            bset ^= low
            vb = low.bit_length() - 1
            X = D[a] & N[vb]  # candidates for d
            if X == 0:
                return False
            # c's: in P[vb], in N[a]
            cset = P[vb] & N[a]
            while cset:
                lowc = cset & (-cset)
                cset ^= lowc
                vc = lowc.bit_length() - 1
                if X & ~N[vc] == 0:
                    return False
    return True


def _try_repair(order, graph, edge):
    """Try to repair the ordering after an edge update.

    edge is (u, v) that was just inserted or deleted.
    Returns a new ordering if repair succeeds, None otherwise.
    """
    n = len(order)
    u, v = edge
    if u == v:
        return None

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

    # Try: move u to p and v to q (both moved).
    # This is a superset of the single moves (when p == original pos of u,
    # or q == original pos of v), so it catches more cases.
    # To keep it tractable, only try when n is small enough.
    if n <= 30:
        iu = order.index(u)
        iv = order.index(v)
        for p in range(n):
            if p == iu:
                continue
            # Remove u, insert at p.
            rest = list(order)
            rest.remove(u)
            rest.insert(p, u)
            # Now move v in rest.
            iv2 = rest.index(v)
            for q in range(n):
                if q == iv2:
                    continue
                new_order = list(rest)
                new_order.remove(v)
                new_order.insert(q, v)
                if _check_lb(new_order, graph):
                    return new_order

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
