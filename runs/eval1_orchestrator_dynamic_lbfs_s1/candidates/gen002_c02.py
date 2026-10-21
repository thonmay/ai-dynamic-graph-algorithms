"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On an update, try to repair the
existing ordering locally (cheap); if the local repair fails, fall back to a
full static LexBFS recomputation (correct, O(n^2) with adjacency matrix).

Local repair idea:
- After an edge insertion (u,v), the only way the old ordering can become
  invalid is via the 4-point property (LB): for some a<b<c with ac in E, ab
  not in E, no d<a has db in E and dc not in E. The new edge can only help
  such witnesses, so an insertion can only break validity if... actually an
  insertion adds edges, which can only create new violations of the form
  "ac in E, ab not in E" (new ac edge) and can only destroy witnesses (new
  dc edge). So insertions CAN break validity.
- After an edge deletion (u,v), the deleted edge can destroy witnesses
  (db or dc was the deleted edge), so deletions can also break validity.

Rather than reason case by case, we do a cheap local fix attempt:
  1. Try the current ordering: verify (LB) property in O(n^3) worst case but
     usually fast; if valid, done.
  2. Try a few cheap re-orderings derived from the old one (e.g. move the
     updated vertices to the front, or run a single LexBFS pass seeded from
     the old ordering's first vertex).
  3. Fall back to full static LexBFS.

Verification of (LB): for all a<b<c (positions in ordering) with
ordering[a] adjacent to ordering[c] and not to ordering[b], there must exist
d<a with ordering[d] adjacent to ordering[b] and not to ordering[c].
We implement this with bitsets (Python ints) for speed: O(n^2) bit ops.
"""


def _adj_bitsets(graph):
    n = len(graph)
    bits = [0] * n
    for i in range(n):
        row = graph[i]
        b = 0
        for j in range(n):
            if row[j]:
                b |= 1 << j
        bits[i] = b
    return bits


def _is_lexbfs(order, bits):
    """Check (LB) 4-point property. order: list of vertices, bits: adj bitsets."""
    n = len(order)
    # pos[v] = position of v in order
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    # For each pair (b, c) with b < c in order:
    #   let S = { a < b : a adjacent to c and not to b }  -> violation candidates
    #   need: exists d < a ... rephrase:
    # For all a<b<c: if adj(a,c) and not adj(a,b): exists d<a: adj(d,b) and not adj(d,c)
    # Equivalent: for all b<c: for all a<b with adj(a,c) and not adj(a,b):
    #   ( {d<a : adj(d,b) and not adj(d,c)} is nonempty )
    # For fixed b,c: define for each a<b: bad(a) = adj(a,c) and not adj(a,b).
    #   good(a) = exists d<a with adj(d,b) and not adj(d,c).
    # good(a) holds iff (prefix of vertices before a) intersects (N(b) \ N(c)).
    # Let W = N(b) \ N(c) (bitmask). For a to be good, W must contain some vertex
    # that appears before a in the order.
    # So: for all a<b with bad(a): W must have a vertex at position < pos[a].
    # Precompute for each position p the bitmask of vertices at positions < p.
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])
    for bi in range(n):
        b = order[bi]
        Nb = bits[b]
        for ci in range(bi + 1, n):
            c = order[ci]
            Nc = bits[c]
            W = Nb & ~Nc
            if W == 0:
                continue
            # For each a at position ai < bi with adj(a,c) and not adj(a,b):
            #   need W & prefix[ai] != 0
            # a must be in N(c) \ N(b) = Nc & ~Nb, and position < bi.
            A = Nc & ~Nb
            # iterate positions ai < bi where order[ai] in A
            for ai in range(bi):
                a = order[ai]
                if (A >> a) & 1:
                    if (W & prefix[ai]) == 0:
                        return False
    return True


def _lexbfs_full(graph):
    """Static LexBFS via partition refinement, O(n^2) with bitsets.

    Standard HMPV algorithm: maintain an ordered list of buckets of
    unprocessed vertices.  Repeatedly take the first vertex of the first
    bucket, append it to the order, and refine every remaining bucket by
    adjacency to that vertex (neighbors first, then non-neighbors).
    """
    n = len(graph)
    bits = _adj_bitsets(graph)
    full_mask = (1 << n) - 1
    # buckets: list of sets (as bitmasks) of unprocessed vertices, ordered.
    # Start: one bucket with all vertices.
    buckets = [full_mask]
    order = []
    while buckets:
        # take the first vertex of the first bucket
        b = buckets[0]
        v = (b & -b).bit_length() - 1  # lowest set bit
        order.append(v)
        rest = b & ~(1 << v)
        # refine remaining buckets by adjacency to v
        Nv = bits[v]
        new_buckets = []
        for bb in buckets[1:]:
            nb = bb & Nv
            nb2 = bb & (~Nv) & full_mask
            if nb:
                new_buckets.append(nb)
            if nb2:
                new_buckets.append(nb2)
        if rest:
            new_buckets.append(rest)
        buckets = new_buckets
    return order


def _lexbfs_from(graph, start):
    """Static LexBFS via partition refinement, O(n^2) with bitsets.

    Standard HMPV algorithm: maintain an ordered list of buckets of
    unprocessed vertices.  Repeatedly take the first vertex of the first
    bucket, append it to the order, and refine every remaining bucket by
    adjacency to that vertex (neighbors first, then non-neighbors).
    """
    n = len(graph)
    bits = _adj_bitsets(graph)
    full_mask = (1 << n) - 1
    # buckets: list of sets (as bitmasks) of unprocessed vertices, ordered.
    # Start: one bucket with all vertices.
    buckets = [full_mask]
    order = []
    while buckets:
        # take the first vertex of the first bucket
        b = buckets[0]
        v = (b & -b).bit_length() - 1  # lowest set bit
        order.append(v)
        rest = b & ~(1 << v)
        # refine remaining buckets by adjacency to v
        Nv = bits[v]
        new_buckets = []
        for bb in buckets[1:]:
            nb = bb & Nv
            nb2 = bb & (~Nv) & full_mask
            if nb:
                new_buckets.append(nb)
            if nb2:
                new_buckets.append(nb2)
        if rest:
            new_buckets.append(rest)
        buckets = new_buckets
    return order


def _lexbfs_full(graph):
    return _lexbfs_from(graph, 0)


def init(graph):
    order = _lexbfs_full(graph)
    return {'ordering': order}


def _try_repair(graph, edge, state):
    """Try cheap local repairs; return ordering or None."""
    n = len(graph)
    bits = _adj_bitsets(graph)
    u, v = edge
    old = state['ordering']

    candidates = []
    # 1. old ordering as-is
    candidates.append(list(old))
    # 2. old ordering with u and v moved to front (in old relative order)
    rest = [x for x in old if x not in (u, v)]
    front = [x for x in old if x in (u, v)]
    candidates.append(front + rest)
    # 3. old ordering with u,v moved to front, reversed
    candidates.append(list(reversed(front)) + rest)
    # 4. LexBFS seeded: run full lexbfs but it's O(n^2); skip here, that's the fallback.

    # 5. LexBFS starting from each of u and v (cheap for small n, and the
    #    updated vertices are the natural candidates for a new start).
    for start in (u, v):
        cand = _lexbfs_from(graph, start)
        if _is_lexbfs(cand, bits):
            return cand

    for cand in candidates:
        if _is_lexbfs(cand, bits):
            return cand
    return None


def insert_edge(graph, edge, state):
    order = _try_repair(graph, edge, state)
    if order is None:
        order = _lexbfs_full(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = _try_repair(graph, edge, state)
    if order is None:
        order = _lexbfs_full(graph)
    return {'ordering': order}
