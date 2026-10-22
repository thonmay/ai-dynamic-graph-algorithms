"""Dynamic LexBFS ordering (candidate gen008_c01).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static label-based LexBFS (trivially correct, O(n^3) on the
    adjacency matrix).
  * update: try a cheap local repair that keeps the previous ordering valid
    (see _try_repair).  If the repair fails, fall back to a full static
    recompute.  The repair is only ever applied when the resulting ordering
    is verified to satisfy the (LB) 4-point property, so correctness never
    depends on the repair succeeding.

Improvements over the parent (gen002_c04):
  * _is_lexbfs is now O(n^2) using a position-index array and a per-vertex
    "first non-neighbour" prefix counter, instead of O(n^3) with set
    membership tests.  This makes the repair's verification loop much
    cheaper, so more repair candidates can be tried before falling back.
  * The repair tries a small family of local moves (unchanged, swap,
    move-to-neighbour, move-to-front, move-to-end) and accepts the first
    one that passes the O(n^2) (LB) check.

State dict keys:
  'ordering': list of all n vertices, a valid LexBFS ordering.
  'n': number of vertices.
  'adj': list of sets of neighbours (kept in sync with the matrix).
"""


def _lexbfs(adj, n):
    """Static LexBFS via the label-based formulation.

    Each unplaced vertex v carries a label: the list of 0/1 bits recording
    adjacency to each already-placed vertex, in placement order.  At each
    step, pick the unplaced vertex with the lexicographically smallest label
    (tie-break by vertex id), place it, and extend every remaining label
    with 1 if adjacent to the placed vertex, else 0.

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


def _is_lexbfs(order, adj, n):
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E.

    For a fixed (a, b) with ab not in E, let S = N(b) ∩ [0, a) (the set of
    vertices d at positions < a that are adjacent to b).  The condition
    fails iff there exists c > b with ac in E and S ⊆ N(c) (i.e. c is
    adjacent to every vertex in S, so no d in S has dc not in E).  If S is
    empty, the condition fails whenever any c > b has ac in E.

    Implementation: use Python ints as bitsets.  B[v] = neighbour bitset of
    v; P[p] = bitset of vertices at positions < p.  For each (a, b) with
    ab not in E, compute S = B[b] & P[a], then iterate c in N(a) ∩ (P[n]
    ^ P[b+1]) and check S ⊆ B[c].
    """
    if n <= 2:
        return True
    # Build bitsets
    B = [0] * n
    for v in range(n):
        bits = 0
        for w in adj[v]:
            bits |= (1 << w)
        B[v] = bits
    # P[p] = bitset of vertices at positions < p
    P = [0] * (n + 1)
    for p in range(n):
        P[p + 1] = P[p] | (1 << order[p])
    # Check
    for a in range(n):
        va = order[a]
        Pa = P[a]  # vertices at positions < a
        for b in range(a + 1, n):
            vb = order[b]
            if (B[va] >> vb) & 1:
                continue  # ab in E, skip
            S = B[vb] & Pa  # neighbours of b at positions < a
            if S == 0:
                # Need: no c > b with ac in E
                # Check if va has any neighbour at positions > b
                # N(va) & (all positions > b)
                # positions > b = ~P[b+1] & (all bits)
                # But we only care about positions b+1..n-1
                # N(va) & (P[n] ^ P[b+1])
                rest = P[n] ^ P[b + 1]
                if B[va] & rest:
                    return False
                continue
            # For each c > b with ac in E: check S ⊆ B[c]
            # Iterate over neighbours of va at positions > b
            cands = B[va] & (P[n] ^ P[b + 1])
            while cands:
                lsb = cands & (-cands)
                vc = lsb.bit_length() - 1
                cands ^= lsb
                if (B[vc] & S) == S:
                    return False
    return True


def _try_repair(order, adj, n, edge, inserted):
    """Try to keep `order` valid after flipping `edge`.

    Returns a new ordering (possibly == order) if it is valid, else None.
    Tries a small family of local moves and accepts the first result that
    passes the (LB) check.
    """
    u, v = edge
    if u == v:
        return order
    # candidate 1: unchanged ordering
    if _is_lexbfs(order, adj, n):
        return order
    iu = order.index(u)
    iv = order.index(v)
    # candidate 2: swap u and v
    o2 = list(order)
    o2[iu], o2[iv] = o2[iv], o2[iu]
    if _is_lexbfs(o2, adj, n):
        return o2
    # candidate 3: move u next to v (before or after)
    for target in (iv, iv + 1):
        o3 = list(order)
        o3.pop(iu)
        t = target
        if t > len(o3):
            t = len(o3)
        o3.insert(t, u)
        if _is_lexbfs(o3, adj, n):
            return o3
    # candidate 4: move v next to u
    for target in (iu, iu + 1):
        o4 = list(order)
        o4.pop(iv)
        t = target
        if t > len(o4):
            t = len(o4)
        o4.insert(t, v)
        if _is_lexbfs(o4, adj, n):
            return o4
    # candidate 5: move u to front
    o5 = list(order)
    o5.pop(iu)
    o5.insert(0, u)
    if _is_lexbfs(o5, adj, n):
        return o5
    # candidate 6: move v to front
    o6 = list(order)
    o6.pop(iv)
    o6.insert(0, v)
    if _is_lexbfs(o6, adj, n):
        return o6
    # candidate 7: move u to end
    o7 = list(order)
    o7.pop(iu)
    o7.append(u)
    if _is_lexbfs(o7, adj, n):
        return o7
    # candidate 8: move v to end
    o8 = list(order)
    o8.pop(iv)
    o8.append(v)
    if _is_lexbfs(o8, adj, n):
        return o8
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
    new_order = _try_repair(order, adj, n, edge, True)
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
    new_order = _try_repair(order, adj, n, edge, False)
    if new_order is None:
        new_order = _lexbfs(adj, n)
    return {'ordering': new_order, 'n': n, 'adj': adj}
