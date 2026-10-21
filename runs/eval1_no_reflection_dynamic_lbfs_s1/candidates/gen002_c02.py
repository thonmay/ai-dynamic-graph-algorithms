"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via bucket lists.
- insert_edge(u,v): if the current ordering is still valid (checked by the
  (LB) 4-point property, O(n^2)), keep it. Otherwise recompute.
- delete_edge(u,v): if the current ordering is still valid, keep it.
  Otherwise recompute.

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.

This is correct but may recompute often; the validity check is the cheap
filter that avoids recomputation when the update does not break the
ordering.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of lists of vertices, in label order.
    # Standard HMPV: pick the first vertex of the first non-empty bucket,
    # append it to the ordering, then split every bucket by adjacency to it
    # (adjacent part first, then non-adjacent part).
    buckets = [[v for v in range(n)]]
    ordering = []

    while len(ordering) < n:
        # find first non-empty bucket
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        v = buckets[bi].pop(0)
        ordering.append(v)

        # split every bucket by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                new_buckets.append([])
                continue
            nb = [x for x in b if graph[v][x]]
            nnb = [x for x in b if not graph[v][x]]
            # nb goes first (adjacent to v), then nnb
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
            if not nb and not nnb:
                new_buckets.append([])
        buckets = new_buckets

    return ordering


def _lexbfs_from(graph, start):
    """Static LexBFS starting from a specific vertex. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of lists of vertices, in label order.
    # Start with the given vertex first in the first bucket.
    buckets = [[start] + [v for v in range(n) if v != start]]
    ordering = []

    while len(ordering) < n:
        # find first non-empty bucket
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        v = buckets[bi].pop(0)
        ordering.append(v)

        # split every bucket by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                new_buckets.append([])
                continue
            nb = [x for x in b if graph[v][x]]
            nnb = [x for x in b if not graph[v][x]]
            # nb goes first (adjacent to v), then nnb
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
            if not nb and not nnb:
                new_buckets.append([])
        buckets = new_buckets

    return ordering


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Bitset implementation: for each b, precompute
      min_d_pos[b][c] = min{ pos[d] : db in E, dc not in E, pos[d] < pos[b] }
    (infinity if none), for bc in E with pos[b] < pos[c].  Then the triple
    (a, b, c) is valid iff min_d_pos[b][c] < pos[a].
    """
    n = len(ordering)
    if n == 0:
        return True

    # pos[v] = position of v in ordering
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    # Bitsets of adjacency, indexed by position in the ordering.
    # adj_bits[p] = bitmask of positions q with ordering[p] adjacent to ordering[q].
    adj_bits = [0] * n
    for p in range(n):
        v = ordering[p]
        row = graph[v]
        bits = 0
        for q in range(n):
            if row[ordering[q]]:
                bits |= (1 << q)
        adj_bits[p] = bits

    INF = n + 1
    # min_d_pos indexed by (position of b, position of c)
    min_d_pos = [[INF] * n for _ in range(n)]

    for pb in range(n):
        b = ordering[pb]
        # d must have pos[d] < pb: mask of positions < pb
        pred_mask = (1 << pb) - 1
        # d must be adjacent to b: adj_bits[pb]
        # d must NOT be adjacent to c: ~adj_bits[pc]
        for pc in range(pb + 1, n):
            if not (adj_bits[pb] >> pc) & 1:
                continue  # bc not in E
            c = ordering[pc]
            # candidates: d < pb, db in E, dc not in E
            cand = pred_mask & adj_bits[pb] & ~adj_bits[pc]
            if cand:
                # min position = index of lowest set bit
                min_d_pos[pb][pc] = (cand & -cand).bit_length() - 1

    # Check all triples a < b < c with ac in E, ab not in E
    for pa in range(n):
        a = ordering[pa]
        for pb in range(pa + 1, n):
            b = ordering[pb]
            if (adj_bits[pa] >> pb) & 1:
                continue  # ab in E, skip
            # ab not in E, pa < pb
            for pc in range(pb + 1, n):
                if not (adj_bits[pa] >> pc) & 1:
                    continue  # ac not in E, skip
                # ac in E, ab not in E, pa < pb < pc
                # need exists d < a: db in E, dc not in E
                # i.e., min_d_pos[pb][pc] < pa
                if min_d_pos[pb][pc] >= pa:
                    return False
    return True


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Try to find a valid ordering by starting from different vertices.
    # The current ordering's first vertex is a good candidate.
    n = len(ordering)
    # Try the first few vertices of the current ordering as starts.
    for i in range(min(3, n)):
        candidate = _lexbfs_from(graph, ordering[i])
        if _is_valid_lexbfs(graph, candidate):
            return {'ordering': candidate}
    # Fallback: full recompute with default start.
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    # Try to find a valid ordering by starting from different vertices.
    n = len(ordering)
    for i in range(min(3, n)):
        candidate = _lexbfs_from(graph, ordering[i])
        if _is_valid_lexbfs(graph, candidate):
            return {'ordering': candidate}
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
