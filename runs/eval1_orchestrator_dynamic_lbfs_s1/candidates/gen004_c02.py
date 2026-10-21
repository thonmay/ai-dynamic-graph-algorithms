"""Dynamic LexBFS ordering (open problem; correctness-first candidate).

Strategy: maintain a valid LexBFS ordering.  After each update, try to
repair the existing ordering with a local fix (transpositions, small
moves, or a local re-derivation of the tail); if the local fix cannot
restore validity, fall back to a full O(n^2) partition-refinement
recomputation.

Validity is certified by the (LB) 4-point property of Corneil and
Krueger: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.
"""


def _check_lexbfs(graph, order):
    """Return True iff `order` is a valid LexBFS ordering of `graph`.

    Uses the (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.
    """
    n = len(order)
    adj = graph
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb]:
                continue  # ab in E: condition vacuous
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if not adj[va][vc]:
                    continue
                # need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = order[d]
                    if adj[vd][vb] and not adj[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _lexbfs_full(graph):
    """Full O(n^2) LexBFS via partition refinement with buckets.

    Returns a valid LexBFS ordering (deterministic tie-break by vertex id).
    """
    n = len(graph)
    if n == 0:
        return []
    # Classic LexBFS:
    #   - maintain buckets (lists of vertices) in order; all vertices in
    #     the same bucket have identical labels (sets of already-ordered
    #     neighbors).
    #   - pick the first vertex of the first bucket, order it, then
    #     refine every bucket by adjacency to the picked vertex.
    #
    # We use the standard formulation where the label of a vertex is the
    # set of its neighbors that have already been ordered.  Two vertices
    # are in the same bucket iff they have the same label.  When we order
    # vertex v, we split each bucket into the part adjacent to v (label
    # gains v) and the part not adjacent to v (label unchanged).  The
    # adjacent part comes first (it has the "1" bit for v).
    #
    # Tie-breaking: within a bucket, vertices are ordered by vertex id
    # (smallest first).  This gives a deterministic valid LexBFS.

    # buckets: list of lists of vertices, in order.
    # Initially one bucket containing all vertices (all labels empty).
    buckets = [list(range(n))]

    ordered = []
    while buckets:
        # take first vertex of first bucket
        b = buckets[0]
        v = b[0]
        b.remove(v)
        if not b:
            buckets.pop(0)
        ordered.append(v)
        # refine all buckets by adjacency to v
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            adj_part = [x for x in bucket if graph[v][x]]
            non_part = [x for x in bucket if not graph[v][x]]
            # adjacent part first (they get the 1 bit for v)
            if adj_part:
                new_buckets.append(adj_part)
            if non_part:
                new_buckets.append(non_part)
        buckets = new_buckets
    return ordered


def _lexbfs_from(graph, prefix):
    """LexBFS continuation: given a prefix (list of vertices already
    ordered), complete the ordering by running partition refinement on
    the remaining vertices, seeded with the labels induced by the
    prefix.

    Returns the full ordering (prefix + completion).  The caller must
    verify the result with _check_lexbfs; if the prefix is not a valid
    LexBFS prefix, the result will fail the check.
    """
    n = len(graph)
    prefix = list(prefix)
    if len(prefix) == n:
        return prefix
    in_prefix = set(prefix)
    rem = [x for x in range(n) if x not in in_prefix]
    labels = {}
    for x in rem:
        labels[x] = tuple(p for p in prefix if graph[p][x])
    # buckets: group remaining vertices by label, in lexicographic order
    # of the label tuple (0 < 1 at each prefix position).
    groups = {}
    for x in rem:
        groups.setdefault(labels[x], []).append(x)
    buckets = [sorted(groups[k]) for k in sorted(groups.keys())]
    ordered = list(prefix)
    while buckets:
        b = buckets[0]
        v = b[0]
        b.remove(v)
        if not b:
            buckets.pop(0)
        ordered.append(v)
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            adj_part = [x for x in bucket if graph[v][x]]
            non_part = [x for x in bucket if not graph[v][x]]
            if adj_part:
                new_buckets.append(adj_part)
            if non_part:
                new_buckets.append(non_part)
        buckets = new_buckets
    return ordered


def _try_transpose(order, u, v):
    """Return a new order with u and v swapped, or None if not adjacent
    in the order."""
    pos = {x: i for i, x in enumerate(order)}
    i, j = pos[u], pos[v]
    if abs(i - j) != 1:
        return None
    new = list(order)
    new[i], new[j] = new[j], new[i]
    return new


def _repair(graph, order, edge):
    """Try to repair `order` after flipping `edge`.  Return a valid
    ordering or None."""
    u, v = edge
    if _check_lexbfs(graph, order):
        return order
    # try transposition of u and v if adjacent in order
    cand = _try_transpose(order, u, v)
    if cand is not None and _check_lexbfs(graph, cand):
        return cand
    # try moving the later of u,v just before the earlier one
    pos = {x: i for i, x in enumerate(order)}
    i, j = pos[u], pos[v]
    if i > j:
        i, j = j, i  # i is earlier position, j later
    # move vertex at position j to position i
    new = list(order)
    x = new.pop(j)
    new.insert(i, x)
    if _check_lexbfs(graph, new):
        return new
    # local re-derivation: keep the longest valid prefix of the old
    # order, then complete it with a fresh partition refinement.
    for k in range(len(order) - 1, 0, -1):
        prefix = order[:k]
        full = _lexbfs_from(graph, prefix)
        if _check_lexbfs(graph, full):
            return full
    return None


def init(graph):
    order = _lexbfs_full(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    fixed = _repair(graph, order, edge)
    if fixed is None:
        fixed = _lexbfs_full(graph)
    return {'ordering': fixed}


def delete_edge(graph, edge, state):
    order = state['ordering']
    fixed = _repair(graph, order, edge)
    if fixed is None:
        fixed = _lexbfs_full(graph)
    return {'ordering': fixed}
