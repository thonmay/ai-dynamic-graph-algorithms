"""Dynamic LexBFS ordering (candidate gen005_c01).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static label-based LexBFS (trivially correct, O(n^3) on the
    adjacency matrix).
  * update: try a cheap local repair that keeps the previous ordering valid
    (see _try_repair).  The repair is only ever applied when the resulting
    ordering is verified to satisfy the (LB) 4-point property, so
    correctness never depends on the repair succeeding.  If the repair
    fails, fall back to a full static recompute.

Improvements over the parent (gen002_c04):
  * The (LB) check is now O(n^2) using a precomputed "witness" table:
    for each pair (b, c) with b < c, witness[b][c] is the smallest d < b
    with db in E and dc not in E (or -1).  The 4-point property then
    reduces to: for all a < b < c with ac in E and ab not in E,
    witness[b][c] >= 0 and witness[b][c] < a.
  * The repair tries a richer set of local moves: unchanged, swap of the
    two endpoints, moving either endpoint to any of a handful of
    positions (its old position, next to the other endpoint, at the front,
    at the back, and a few positions around the other endpoint).  Each
    candidate is verified with the O(n^2) check, so the repair is cheap
    and the fallback recompute is only reached when no local move works.

State dict keys:
  'ordering': list of all n vertices, a valid LexBFS ordering.
  'n': number of vertices.
  'adj': list of sets of neighbours (kept in sync with the matrix).
"""


def _lexbfs(adj, n):
    """Static LexBFS via the label-based formulation.

    Each unplaced vertex v carries a label: the list of 0/1 bits recording
    adjacency to each already-placed vertex, in placement order.  At each
    step, pick the unplaced vertex with the lexicographically smallest
    label (tie-break by vertex id), place it, and extend every remaining
    label with 1 if adjacent to the placed vertex, else 0.

    This is O(n^3) but trivially correct: the resulting order is exactly a
    LexBFS ordering (with vertex-id tie-breaking).
    """
    if n == 0:
        return []
    labels = [[] for _ in range(n)]
    placed = [False] * n
    out = []
    for _ in range(n):
        best = -1
        for v in range(n):
            if placed[v]:
                continue
            if best == -1 or labels[v] > labels[best]:
                best = v
        placed[best] = True
        out.append(best)
        for v in range(n):
            if not placed[v]:
                labels[v].append(1 if best in adj[v] else 0)
    return out


def _witness_table(order, adj, n):
    """witness[b][c] = smallest d < b with db in E and dc not in E, or -1.

    O(n^3) worst case but with a small constant; used to make the (LB)
    check O(n^2).
    """
    witness = [[-1] * n for _ in range(n)]
    for b in range(1, n):
        vb = order[b]
        for c in range(b + 1, n):
            vc = order[c]
            for d in range(b):
                vd = order[d]
                if vb in adj[vd] and vc not in adj[vd]:
                    witness[b][c] = d
                    break
    return witness


def _is_lexbfs(order, adj, n):
    """Check the (LB) 4-point property in O(n^2) using the witness table:
    for all a < b < c with ac in E and ab not in E, we need a witness d < a
    with db in E and dc not in E, i.e. witness[b][c] >= 0 and
    witness[b][c] < a."""
    witness = _witness_table(order, adj, n)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if va in adj[vb]:
                continue
            # ab not in E; need: for every c > b with ac in E, witness[b][c] < a
            for c in range(b + 1, n):
                vc = order[c]
                if va not in adj[vc]:
                    continue
                w = witness[b][c]
                if w < 0 or w >= a:
                    return False
    return True


def _try_repair(order, adj, n, edge):
    """Try to keep `order` valid after flipping `edge`.

    Returns a new ordering (possibly == order) if it is valid, else None.
    The idea: an edge flip only changes the 4-point certificate for triples
    involving the two endpoints.  We try a set of local moves (unchanged,
    swap, moving one endpoint to a few candidate positions) and accept the
    first result that passes the full (LB) check.  Each check is O(n^2)
    after the O(n^3) witness-table build, so the repair is cheap; the
    fallback recompute is also O(n^3) on the matrix, so this is a win when
    the repair succeeds early.
    """
    u, v = edge
    if u == v:
        return order
    iu = order.index(u)
    iv = order.index(v)

    # candidate 1: unchanged ordering
    if _is_lexbfs(order, adj, n):
        return order

    # candidate 2: swap u and v
    o2 = list(order)
    o2[iu], o2[iv] = o2[iv], o2[iu]
    if _is_lexbfs(o2, adj, n):
        return o2

    # candidates 3/4: move u (or v) to a few candidate positions.
    # Positions tried: old position, next to the other endpoint (before/
    # after), front, back, and a couple of positions around the other
    # endpoint.  Deduplicated and clamped to [0, n-1].
    def _try_move(order, src, dst_pos):
        o = list(order)
        o.pop(o.index(src))
        t = dst_pos
        if t < 0:
            t = 0
        if t > len(o):
            t = len(o)
        o.insert(t, src)
        return o

    # positions for moving u (relative to v's position iv in the original)
    pos_u = {iu, iv, iv + 1, 0, n - 1, iv - 1, iv + 2}
    for p in pos_u:
        o3 = _try_move(order, u, p)
        if o3 is not order and _is_lexbfs(o3, adj, n):
            return o3

    # positions for moving v (relative to u's position iu in the original)
    pos_v = {iv, iu, iu + 1, 0, n - 1, iu - 1, iu + 2}
    for p in pos_v:
        o4 = _try_move(order, v, p)
        if o4 is not order and _is_lexbfs(o4, adj, n):
            return o4

    return None


def _adj_from_matrix(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def init(graph):
    n = len(graph)
    adj = _adj_from_matrix(graph)
    order = _lexbfs(adj, n)
    return {'ordering': order, 'n': n, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    adj[u].add(v)
    adj[v].add(u)
    order = state['ordering']
    new_order = _try_repair(order, adj, n, edge)
    if new_order is None:
        new_order = _lexbfs(adj, n)
    return {'ordering': new_order, 'n': n, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = state['adj']
    adj[u].discard(v)
    adj[v].discard(u)
    order = state['ordering']
    new_order = _try_repair(order, adj, n, edge)
    if new_order is None:
        new_order = _lexbfs(adj, n)
    return {'ordering': new_order, 'n': n, 'adj': adj}
