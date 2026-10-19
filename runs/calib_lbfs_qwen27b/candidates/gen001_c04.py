"""Dynamic LexBFS ordering (candidate gen001_c04).

Maintains a valid LexBFS ordering under single edge insertions/deletions.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- update: try a cheap local repair (move one of the two affected vertices to
  a different position). If the repaired ordering is certified valid by the
  (LB) 4-point property, keep it. Otherwise fall back to a full recompute.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
We use it as a certificate of validity, so the state is always a valid
LexBFS ordering.
"""

import sys

sys.setrecursionlimit(100000)


# ---------------------------------------------------------------------------
# Static LexBFS (partition refinement, O(n+m))
# ---------------------------------------------------------------------------

def _lexbfs_static(adj):
    """Return a valid LexBFS ordering of the undirected graph given by
    adjacency matrix `adj` (list of lists of 0/1)."""
    n = len(adj)
    if n == 0:
        return []
    # adjacency sets
    N = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                N[u].add(v)
                N[v].add(u)

    # buckets: list of sets, each bucket is a set of vertices
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # pick first non-empty bucket
        i = 0
        while i < len(buckets) and not buckets[i]:
            i += 1
        if i == len(buckets):
            break
        B = buckets[i]
        # choose smallest vertex in B
        v = min(B)
        B.remove(v)
        order.append(v)
        # refine each bucket by adjacency to v
        new_buckets = []
        for C in buckets:
            if not C:
                continue
            Cn = set()
            Cnot = set()
            for x in C:
                if x in N[v]:
                    Cn.add(x)
                else:
                    Cnot.add(x)
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets
    return order


# ---------------------------------------------------------------------------
# (LB) 4-point property check
# ---------------------------------------------------------------------------

def _is_valid_lexbfs(order, adj):
    """Check the (LB) property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E."""
    n = len(order)
    if n <= 2:
        return True
    # neighbor sets
    N = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                N[u].add(v)
                N[v].add(u)

    # For each pair (b, c) with pos[b] < pos[c]:
    #   A = {a : pos[a] < pos[b], a~c, a not~ b}
    #   if A nonempty, let a0 = min pos in A; need exists d < pos[a0]
    #   with d~b and d not~ c.
    for ci in range(n):
        c = order[ci]
        Nc = N[c]
        for bi in range(ci):
            b = order[bi]
            Nb = N[b]
            # find a: pos < bi, a in Nc, a not in Nb
            a0 = None
            for ai in range(bi):
                a = order[ai]
                if a in Nc and a not in Nb:
                    a0 = ai
                    break
            if a0 is None:
                continue
            # need d < a0 with d in Nb and d not in Nc
            ok = False
            for di in range(a0):
                d = order[di]
                if d in Nb and d not in Nc:
                    ok = True
                    break
            if not ok:
                return False
    return True


# ---------------------------------------------------------------------------
# Local repair: try to move one vertex to a better position
# ---------------------------------------------------------------------------

def _try_local_repair(order, adj, moved):
    """Try to produce a valid ordering by moving `moved` to a different
    position. Returns a new ordering or None."""
    n = len(order)
    if n <= 2:
        return order
    cur = order.index(moved)
    # Try positions in order of distance from current position.
    for d in range(1, n):
        for p in (cur - d, cur + d):
            if 0 <= p < n:
                new_order = order[:cur] + order[cur + 1:]
                new_order.insert(p, moved)
                if _is_valid_lexbfs(new_order, adj):
                    return new_order
    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def init(graph):
    order = _lexbfs_static(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    # Try local repair: move u or v.
    for moved in (u, v):
        new_order = _try_local_repair(order, graph, moved)
        if new_order is not None:
            return {'ordering': new_order}
    # Fallback: full recompute.
    order = _lexbfs_static(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    for moved in (u, v):
        new_order = _try_local_repair(order, graph, moved)
        if new_order is not None:
            return {'ordering': new_order}
    order = _lexbfs_static(graph)
    return {'ordering': order}
