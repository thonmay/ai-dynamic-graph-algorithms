"""Dynamic LexBFS ordering (candidate gen002_c05).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core: after any update, if the previously maintained ordering
is no longer a valid LexBFS ordering, recompute a fresh one with the
standard O(n^2) partition-refinement LexBFS.  If it is still valid, keep
it (no recompute).  Validity is checked with the (LB) 4-point property of
Corneil and Krueger: for all positions a < b < c with ac in E and ab not
in E, there exists d < a with db in E and dc not in E.

Improvements over the parent (gen001_c04):
  1. The (LB) check is vectorized with Python ints as bitsets:
     - adj_bits[v]  : bitset of neighbors of v
     - prefix[v]    : bitset of vertices ordered before v
     - suffix[v]    : bitset of vertices ordered after v
     For each non-edge (a, b) with a before b, the (LB) condition is
     (N(a) & S(b)) & N(D) == 0  where D = N(b) & P(a) and N(D) is the
     intersection of N(d) over d in D.  This is O(n^2) bit operations
     instead of O(n^3) set lookups, and is exact.
  2. The static LexBFS uses a bucketed label structure: each unvisited
     vertex's label is a bitset of its ordered neighbors; the minimum
     label is found by scanning the buckets (one per ordered vertex) in
     order, which is O(n^2) total instead of O(n^2 log n) list sorts.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    # adj_bits[v] = bitset of neighbors of v.
    adj_bits = [0] * n
    for i in range(n):
        row = graph[i]
        bits = 0
        for j in range(n):
            if row[j]:
                bits |= 1 << j
        adj_bits[i] = bits

    order = []
    unvisited = (1 << n) - 1
    # label[v] = bitset of ordered neighbors of v (only meaningful while
    # v is unvisited).
    label = [0] * n
    # buckets[k] = bitset of unvisited vertices whose label is exactly
    # (1 << k).  A vertex's label is always a subset of the ordered set,
    # so its highest set bit is the last ordered vertex that is a
    # neighbor; the lexicographically smallest label is found by scanning
    # k from 0 upward and taking the smallest vertex id in the first
    # non-empty bucket.  The empty label lives in bucket 0, since
    # 0.bit_length() - 1 == 0.
    buckets = [0] * n
    buckets[0] = unvisited  # all labels start empty

    for _ in range(n):
        # Find the unvisited vertex with the lexicographically smallest
        # label; ties broken by vertex id.
        best = -1
        for k in range(n):
            b = buckets[k]
            if b:
                best = (b & -b).bit_length() - 1
                break
        if best < 0:
            # Should not happen: unvisited is non-empty.
            best = (unvisited & -unvisited).bit_length() - 1

        order.append(best)
        unvisited &= ~(1 << best)
        # Update labels of unvisited neighbors of best: they all gain
        # bit `best`.  Move them to the bucket indexed by their new
        # highest set bit.
        nbrs = adj_bits[best] & unvisited
        while nbrs:
            low = nbrs & -nbrs
            u = low.bit_length() - 1
            nbrs ^= low
            old = label[u]
            new = old | (1 << best)
            label[u] = new
            buckets[old.bit_length() - 1] &= ~low
            buckets[new.bit_length() - 1] |= low

    return order


def _is_valid_lexbfs(order, graph):
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(order)
    if n == 0:
        return True

    # adj_bits[v] = bitset of neighbors of v.
    adj_bits = [0] * n
    for i in range(n):
        row = graph[i]
        bits = 0
        for j in range(n):
            if row[j]:
                bits |= 1 << j
        adj_bits[i] = bits

    # prefix[v] = bitset of vertices ordered before v.
    prefix = [0] * n
    acc = 0
    for v in order:
        prefix[v] = acc
        acc |= 1 << v
    # suffix[v] = bitset of vertices ordered after v.
    suffix = [0] * n
    acc = 0
    for v in reversed(order):
        suffix[v] = acc
        acc |= 1 << v

    all_bits = (1 << n) - 1

    # For each ordered pair (a, b) with a before b and ab not in E:
    #   D = N(b) & P(a)          (vertices before a adjacent to b)
    #   C = N(a) & S(b)          (vertices after b adjacent to a)
    #   N(D) = intersection of N(d) over d in D (all ones if D empty).
    #   (LB) requires: for every c in C, some d in D is not adjacent to c,
    #   i.e. c not in N(D) for all c in C, i.e. C & N(D) == 0.
    for i in range(n):
        a = order[i]
        pa = prefix[a]
        na = adj_bits[a]
        for j in range(i + 1, n):
            b = order[j]
            if (na >> b) & 1:
                continue  # ab in E: no constraint
            # D = N(b) & P(a)
            D = adj_bits[b] & pa
            # N(D) = intersection of adj_bits[d] for d in D.
            if D == 0:
                nd = all_bits
            else:
                nd = all_bits
                d = D
                while d:
                    low = d & -d
                    v = low.bit_length() - 1
                    d ^= low
                    nd &= adj_bits[v]
                    if nd == 0:
                        break
            # C = N(a) & S(b)
            C = na & suffix[b]
            if C & nd:
                return False
    return True


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    # Check if the old ordering is still valid.
    if _is_valid_lexbfs(order, graph):
        return state
    # Recompute.
    order = _lexbfs(graph)
    return {'ordering': order, 'n': state['n']}


def delete_edge(graph, edge, state):
    order = state['ordering']
    # Check if the old ordering is still valid.
    if _is_valid_lexbfs(order, graph):
        return state
    # Recompute.
    order = _lexbfs(graph)
    return {'ordering': order, 'n': state['n']}
