"""Dynamic LexBFS ordering (candidate gen001_c01).

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

    Works in *position* space (not vertex-id space).  For every triple of
    positions i < j < k with a=order[i], b=order[j], c=order[k], the (LB)
    property requires a witness d at position < i with db in E and dc not
    in E whenever a and b have a different adjacency relation to c.  Both
    orientations are checked:
      - ab in E, ac not in E  (c in N(b) \\ N(a))
      - ab not in E, ac in E  (c in N(a) \\ N(b))
    """
    n = len(order)
    # P[i] = bitset of vertices at positions < i.
    P = [0] * (n + 1)
    acc = 0
    for i in range(n):
        P[i] = acc
        acc |= 1 << order[i]
    # after[j] = bitset of vertices at positions > j.
    after = [0] * n
    for j in range(n):
        after[j] = acc & ~((1 << (j + 1)) - 1)
    for i in range(n):
        a = order[i]
        na = bs[a]
        prefix = P[i]
        for j in range(i + 1, n):
            b = order[j]
            nb = bs[b]
            # c after b with a different adjacency relation to a than b has.
            cands = after[j] & (na ^ nb)
            c = cands
            while c:
                lsb = c & -c
                c ^= lsb
                cc = lsb.bit_length() - 1
                # witness d < a: d~b and not d~c.
                if (nb & ~bs[cc] & prefix) == 0:
                    return False
    return True


def _certify_ref(order, graph):
    """Reference (LB) check in position space, O(n^4), for cross-checking."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            for k in range(j + 1, n):
                c = order[k]
                ab = bool(graph[a][b])
                ac = bool(graph[a][c])
                if ab == ac:
                    continue
                ok = False
                for d in order[:i]:
                    if graph[d][b] and not graph[d][c]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


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
