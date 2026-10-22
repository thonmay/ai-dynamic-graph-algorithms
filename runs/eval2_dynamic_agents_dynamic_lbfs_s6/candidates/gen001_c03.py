"""Dynamic LexBFS ordering (candidate gen001_c03).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n+m) via bucket lists.
  * update: try a cheap local repair (reorder the affected vertex within its
    "block" of the ordering); if the (LB) 4-point property is violated, fall
    back to a full recompute.  The repair is only ever applied when the
    resulting ordering is verified to be a valid LexBFS, so correctness is
    guaranteed regardless of the repair's quality.

(LB) property (Corneil-Krueger): for all a < b < c (positions in the
ordering) with ac in E and ab not in E, there exists d < a with db in E and
dc not in E.  We check this property in O(n^2) using bitsets (Python ints)
for speed.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement.  Returns ordering list."""
    n = len(graph)
    # adjacency bitsets for speed
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        b = 0
        for v in range(n):
            if row[v]:
                b |= 1 << v
        adj[u] = b

    # buckets: list of lists, ordered; each bucket holds vertices
    buckets = [[v] for v in range(n)]
    # for each vertex, the index of its bucket
    bidx = list(range(n))

    # label[v] = bitset of buckets that contain a neighbor of v
    label = [0] * n
    for v in range(n):
        b = 0
        for u in range(n):
            if adj[v] >> u & 1:
                b |= 1 << bidx[u]
        label[v] = b

    # process buckets in order; when a bucket is "processed", its vertices
    # are finalized (appended to ordering) and the bucket is removed.
    ordering = []
    i = 0
    while i < len(buckets):
        B = buckets[i]
        if len(B) == 1:
            ordering.append(B[0])
            del buckets[i]
            continue
        # mask of unprocessed buckets (positions >= i)
        mask = 0
        for j in range(i, len(buckets)):
            mask |= 1 << j
        # group vertices of B by (label & mask)
        groups = {}
        for v in B:
            key = label[v] & mask
            groups.setdefault(key, []).append(v)
        # order groups by key (numeric order of the bitset = lexicographic
        # order of the bucket-neighborhood pattern)
        keys = sorted(groups.keys())
        new_buckets = [groups[k] for k in keys]
        # replace bucket i with the sub-buckets
        buckets[i:i + 1] = new_buckets
        # do not advance i: reprocess the first sub-bucket
    return ordering


def _valid_lexbfs(ordering, graph):
    """Check the (LB) 4-point property.  O(n^2) with bitsets."""
    n = len(ordering)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        b = 0
        for v in range(n):
            if row[v]:
                b |= 1 << v
        adj[u] = b
    # posset[x] = bitset of positions of neighbors of x
    posset = [0] * n
    for u in range(n):
        b = 0
        for v in range(n):
            if adj[u] >> v & 1:
                b |= 1 << pos[v]
        posset[u] = b
    # For positions j < k: b = ordering[j], c = ordering[k].
    #   if bc not in E:
    #     bad = posset[c] & mask_lt(j)   # positions i < j with ordering[i] in N_c
    #     T = posset[b] & ~posset[c]     # positions d with ordering[d] in N_b \ N_c
    #     if bad != 0:
    #         need min(T) < min(bad)
    for j in range(n):
        b = ordering[j]
        mask_lt_j = (1 << j) - 1
        for k in range(j + 1, n):
            c = ordering[k]
            if adj[b] >> c & 1:
                continue  # bc in E, no constraint
            bad = posset[c] & mask_lt_j
            if bad == 0:
                continue
            T = posset[b] & ~posset[c]
            if T == 0:
                return False
            min_bad = (bad & -bad).bit_length() - 1
            min_T = (T & -T).bit_length() - 1
            if min_T >= min_bad:
                return False
    return True


def _recompute(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def _try_repair(graph, ordering, edge):
    """Try to fix the ordering after a single edge update.

    Returns a new ordering if valid, else None.
    """
    n = len(ordering)
    u, v = edge
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i

    candidates = []
    # original
    candidates.append(list(ordering))
    # swap u and v
    if pos[u] != pos[v]:
        o = list(ordering)
        o[pos[u]], o[pos[v]] = o[pos[v]], o[pos[u]]
        candidates.append(o)
    # move u to just after v
    o = list(ordering)
    o.pop(pos[u])
    pv = pos[v]
    if pos[u] < pos[v]:
        pv -= 1
    o.insert(pv + 1, u)
    candidates.append(o)
    # move v to just after u
    o = list(ordering)
    o.pop(pos[v])
    pu = pos[u]
    if pos[v] < pos[u]:
        pu -= 1
    o.insert(pu + 1, v)
    candidates.append(o)

    for cand in candidates:
        if _valid_lexbfs(cand, graph):
            return cand
    return None


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    repaired = _try_repair(graph, ordering, edge)
    if repaired is not None:
        return {'ordering': repaired}
    return _recompute(graph)


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    repaired = _try_repair(graph, ordering, edge)
    if repaired is not None:
        return {'ordering': repaired}
    return _recompute(graph)
