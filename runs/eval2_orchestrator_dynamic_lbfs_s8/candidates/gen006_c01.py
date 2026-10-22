"""Dynamic LexBFS ordering (gen006_c01).

Strategy: maintain a valid LexBFS ordering. On each edge update:
  1. If the current ordering is still valid (fast bitset check), keep it.
  2. Try a cheap local repair: move one of the two affected vertices to any
     position, or swap two vertices.
  3. Fall back to a full O(n^2) LexBFS recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

Key improvement over parent: bitset-based validity check (O(n^3 / word)
instead of O(n^4)), and stronger local repair (all single moves + all
swaps involving affected vertices).
"""


def _build_bitsets(adj):
    """Build adjacency bitsets: adj_bits[v] is an int with bit u set iff adj[v][u]."""
    n = len(adj)
    bits = [0] * n
    for v in range(n):
        b = 0
        row = adj[v]
        for u in range(n):
            if row[u]:
                b |= (1 << u)
        bits[v] = b
    return bits


def _lb_valid_fast(order, adj_bits):
    """Faster validity check using precomputed prefix masks.

    For each a, precompute prefix_mask[a] = bitmask of vertices at positions < a.
    Then for (a, b, c): check (N(vb) & ~N(vc) & prefix_mask[a]) != 0.
    """
    n = len(order)
    if n == 0:
        return True

    # Precompute prefix masks: prefix_mask[a] = bits of order[0..a-1]
    prefix_mask = [0] * (n + 1)
    for a in range(n):
        prefix_mask[a + 1] = prefix_mask[a] | (1 << order[a])

    for a in range(n):
        va = order[a]
        bits_a = adj_bits[va]
        pm = prefix_mask[a]  # vertices before position a
        if pm == 0:
            # No d < a possible, so any (a, b, c) with ac in E and ab not in E is a violation
            # Check: exists b > a, c > b with ac in E and ab not in E
            for b in range(a + 1, n):
                vb = order[b]
                if (bits_a >> vb) & 1:
                    continue  # ab in E
                # ab not in E; check if exists c > b with ac in E
                for c in range(b + 1, n):
                    vc = order[c]
                    if (bits_a >> vc) & 1:
                        return False  # violation: no d < a exists
        else:
            for b in range(a + 1, n):
                vb = order[b]
                if (bits_a >> vb) & 1:
                    continue  # ab in E
                # ab not in E; check if exists c > b with ac in E
                # and for that c, (N(vb) & ~N(vc) & pm) == 0
                bits_vb = adj_bits[vb]
                # We need: for all c > b with ac in E: (bits_vb & ~bits_vc & pm) == 0
                # Equivalently: (bits_vb & pm) ⊆ (∩_{c>b, ac∈E} bits_vc)
                # i.e., (bits_vb & pm) & ~(∩_{c>b, ac∈E} bits_vc) == 0
                # i.e., (bits_vb & pm) & (∪_{c>b, ac∈E} ~bits_vc) == 0
                # i.e., for all c > b with ac in E: (bits_vb & pm & ~bits_vc) == 0
                # Let's compute: for each c > b with ac in E, check bits_vb & pm & ~bits_vc
                # Optimization: if bits_vb & pm == 0, then no violation possible
                if (bits_vb & pm) == 0:
                    continue
                # Check all c > b with ac in E
                for c in range(b + 1, n):
                    vc = order[c]
                    if not ((bits_a >> vc) & 1):
                        continue
                    bits_vc = adj_bits[vc]
                    if (bits_vb & pm & ~bits_vc) != 0:
                        return False
    return True


def _lexbfs(adj):
    """Static LexBFS via partition refinement. O(n^2) with adjacency matrix.

    Returns a list of vertices in LexBFS order.
    """
    n = len(adj)
    if n == 0:
        return []

    # Start with all vertices in one bucket, ordered by vertex id.
    buckets = [[v for v in range(n)]]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket
        while buckets and not buckets[0]:
            buckets.pop(0)
        if not buckets:
            break
        # pick the first vertex in the first bucket
        v = buckets[0].pop(0)
        order.append(v)

        # refine: for each bucket, split into neighbors of v and non-neighbors
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            nb = []
            non_nb = []
            for u in bucket:
                if adj[v][u]:
                    nb.append(u)
                else:
                    non_nb.append(u)
            if nb:
                new_buckets.append(nb)
            if non_nb:
                new_buckets.append(non_nb)
        buckets = new_buckets

    return order


def _try_move(order, adj_bits, cv, candidates):
    """Try moving vertex cv to one of the candidate positions.

    Returns a new order if valid, else None.
    """
    n = len(order)
    old_pos = order.index(cv)
    for new_pos in sorted(candidates):
        if new_pos < 0 or new_pos >= n or new_pos == old_pos:
            continue
        new_order = order[:old_pos] + order[old_pos + 1:]
        new_order.insert(new_pos, cv)
        if _lb_valid_fast(new_order, adj_bits):
            return new_order
    return None


def _try_local_repair(order, adj, adj_bits, u, v):
    """Try to fix the ordering by moving or swapping affected vertices.

    Returns a new order if valid, else None.
    """
    n = len(order)
    if n == 0:
        return order

    # For each affected vertex, try moving it to any position.
    for cv in (u, v):
        if cv not in order:
            continue
        old_pos = order.index(cv)
        # Try all positions
        candidates = set(range(n))
        candidates.discard(old_pos)
        result = _try_move(order, adj_bits, cv, candidates)
        if result is not None:
            return result

    # Try swapping u and v
    if u in order and v in order and u != v:
        new_order = order[:]
        pos_u = new_order.index(u)
        pos_v = new_order.index(v)
        new_order[pos_u], new_order[pos_v] = new_order[pos_v], new_order[pos_u]
        if _lb_valid_fast(new_order, adj_bits):
            return new_order

    # Try swapping each affected vertex with every other vertex
    for cv in (u, v):
        if cv not in order:
            continue
        pos_cv = order.index(cv)
        for i in range(n):
            if i == pos_cv:
                continue
            new_order = order[:]
            new_order[pos_cv], new_order[i] = new_order[i], new_order[pos_cv]
            if _lb_valid_fast(new_order, adj_bits):
                return new_order

    return None


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    adj_bits = _build_bitsets(graph)
    return {'ordering': order, 'adj_bits': adj_bits}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    adj_bits = state['adj_bits']

    # Update bitsets for the new edge
    adj_bits[u] |= (1 << v)
    adj_bits[v] |= (1 << u)

    # 1. If the current ordering is still valid, keep it.
    if _lb_valid_fast(order, adj_bits):
        return {'ordering': order, 'adj_bits': adj_bits}

    # 2. Try local repair
    repaired = _try_local_repair(order, graph, adj_bits, u, v)
    if repaired is not None:
        return {'ordering': repaired, 'adj_bits': adj_bits}

    # 3. Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order, 'adj_bits': adj_bits}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    adj_bits = state['adj_bits']

    # Update bitsets for the removed edge
    adj_bits[u] &= ~(1 << v)
    adj_bits[v] &= ~(1 << u)

    # 1. If the current ordering is still valid, keep it.
    if _lb_valid_fast(order, adj_bits):
        return {'ordering': order, 'adj_bits': adj_bits}

    # 2. Try local repair
    repaired = _try_local_repair(order, graph, adj_bits, u, v)
    if repaired is not None:
        return {'ordering': repaired, 'adj_bits': adj_bits}

    # 3. Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order, 'adj_bits': adj_bits}
