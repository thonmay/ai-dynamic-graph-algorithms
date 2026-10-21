"""Dynamic LexBFS ordering (candidate gen003_c02).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via adjacency sets.
- insert_edge: a new edge can create new (LB) obligations, so validate the
  current ordering with the O(n^2) bitset certificate check; if it still
  certifies, keep it (no recompute); otherwise recompute.
- delete_edge: a deletion can break the certificate, so validate the
  current ordering; if it still certifies, keep it; otherwise recompute.

The certificate (Corneil-Krueger (LB)): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _adj_sets(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    return adj


def _lexbfs(adj):
    """Static LexBFS via partition refinement. Returns the ordering."""
    n = len(adj)
    buckets = [[v] for v in range(n)]
    ordered = []
    for _ in range(n):
        while buckets and not buckets[0]:
            buckets.pop(0)
        if not buckets:
            break
        v = buckets[0].pop(0)
        ordered.append(v)
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            nb = [x for x in bucket if x in adj[v]]
            nnb = [x for x in bucket if x not in adj[v]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets
    return ordered


def _bitsets(graph):
    n = len(graph)
    bs = [0] * n
    for u in range(n):
        row = graph[u]
        x = 0
        for v in range(n):
            if row[v]:
                x |= 1 << v
        bs[u] = x
    return bs


def _certify(order, bs):
    """Check the (LB) 4-point property. Returns True iff valid.

    For all positions a < b < c with ac in E and ab not in E, there exists
    d < a with db in E and dc not in E.
    """
    n = len(order)
    # P[p] = bitset of vertices at positions < p
    P = [0] * (n + 1)
    for p in range(1, n + 1):
        P[p] = P[p - 1] | (1 << order[p - 1])
    # A[p] = bitset of vertices at positions > p
    A = [0] * (n + 1)
    for p in range(n - 1, -1, -1):
        A[p] = A[p + 1]
        if p + 1 < n:
            A[p] |= 1 << order[p + 1]
    for i in range(n):
        a = order[i]
        na = bs[a]
        prefix = P[i]
        for j in range(i + 1, n):
            b = order[j]
            if (na >> b) & 1:
                continue  # a~b: no obligation
            # candidates c after b adjacent to a
            cands = na & A[j]
            if not cands:
                continue
            nb = bs[b]
            c = cands
            while c:
                lsb = c & -c
                c ^= lsb
                cc = lsb.bit_length() - 1
                if (nb & ~bs[cc] & prefix) == 0:
                    return False
    return True


def _certify_debug(order, bs):
    """Return (valid, first_violation) for debugging."""
    n = len(order)
    P = [0] * (n + 1)
    for p in range(1, n + 1):
        P[p] = P[p - 1] | (1 << order[p - 1])
    A = [0] * (n + 1)
    for p in range(n - 1, -1, -1):
        A[p] = A[p + 1]
        if p + 1 < n:
            A[p] |= 1 << order[p + 1]
    for i in range(n):
        a = order[i]
        na = bs[a]
        prefix = P[i]
        for j in range(i + 1, n):
            b = order[j]
            if (na >> b) & 1:
                continue
            cands = na & A[j]
            if not cands:
                continue
            nb = bs[b]
            c = cands
            while c:
                lsb = c & -c
                c ^= lsb
                cc = lsb.bit_length() - 1
                if (nb & ~bs[cc] & prefix) == 0:
                    return False, (a, b, cc, i)
    return True, None


def _certify_debug(order, bs):
    """Return (valid, first_violation) for debugging."""
    n = len(order)
    P = [0] * (n + 1)
    for p in range(1, n + 1):
        P[p] = P[p - 1] | (1 << order[p - 1])
    A = [0] * (n + 1)
    for p in range(n - 1, -1, -1):
        A[p] = A[p + 1]
        if p + 1 < n:
            A[p] |= 1 << order[p + 1]
    for i in range(n):
        a = order[i]
        na = bs[a]
        prefix = P[i]
        for j in range(i + 1, n):
            b = order[j]
            if (na >> b) & 1:
                continue
            cands = na & A[j]
            if not cands:
                continue
            nb = bs[b]
            c = cands
            while c:
                lsb = c & -c
                c ^= lsb
                cc = lsb.bit_length() - 1
                if (nb & ~bs[cc] & prefix) == 0:
                    return False, (a, b, cc, i)
    return True, None


def _recompute(graph):
    adj = _adj_sets(graph)
    order = _lexbfs(adj)
    return {'ordering': order, 'bitsets': _bitsets(graph)}


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    # Adding an edge can create new obligations (a,b,c) where the new edge
    # is a-c and a-b was already a non-edge, so the certificate must be
    # re-checked. If it still holds, keep the ordering; else recompute.
    bs = _bitsets(graph)
    order = state['ordering']
    if _certify(order, bs):
        return {'ordering': order, 'bitsets': bs}
    return _recompute(graph)


def delete_edge(graph, edge, state):
    bs = _bitsets(graph)
    order = state['ordering']
    if _certify(order, bs):
        return {'ordering': order, 'bitsets': bs}
    return _recompute(graph)
