"""Dynamic LexBFS ordering (gen005_c03).

Derived from parent gen005_c02. Changes:
  1. Fast-path for insertions: adding edge (u,v) can only create new
     (LB) violations where the new edge is the 'ac' edge. So we only
     check O(n) triples instead of O(n^2).
  2. Deletions still need the full O(n^2) check (removing an edge can
     destroy witnesses anywhere).
  3. _lexbfs and _check_lb_full kept from parent (correct baseline).
"""


def _bitsets(graph):
    n = len(graph)
    adj = [0] * n
    for i in range(n):
        row = graph[i]
        b = 0
        for j in range(n):
            if row[j]:
                b |= 1 << j
        adj[i] = b
    return adj


def _lexbfs(adj, n):
    """Partition-refinement LexBFS using bitsets. Returns ordering list."""
    if n == 0:
        return []
    order = []
    remaining = (1 << n) - 1
    buckets = [remaining]

    for _ in range(n):
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        B = buckets[bi]
        v = (B & -B).bit_length() - 1
        Bv = 1 << v
        B &= ~Bv
        remaining &= ~Bv
        order.append(v)

        Nv = adj[v]
        new_buckets = []
        for i, C in enumerate(buckets):
            if i == bi:
                C = B
            Cn = C & Nv
            Cnot = C & ~Nv
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets

    return order


def _min_pos_in_set(A, pos):
    """Find the minimum position among vertices in bitset A."""
    min_pa = 1 << 62
    tmp = A
    while tmp:
        lb = tmp & -tmp
        a = lb.bit_length() - 1
        pa = pos[a]
        if pa < min_pa:
            min_pa = pa
        tmp ^= lb
    return min_pa


def _check_lb_full(adj, n, order):
    """Full (LB) 4-point property check. O(n^2) bit ops."""
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    for pb in range(n):
        b = order[pb]
        adjb = adj[b]
        for pc in range(pb + 1, n):
            c = order[pc]
            A = prefix[pb] & ~adjb & adj[c]
            if not A:
                continue
            W = adjb & ~adj[c]
            if not W:
                return False
            min_pa = _min_pos_in_set(A, pos)
            if not (W & prefix[min_pa]):
                return False
    return True


def _check_lb_insert(adj, n, order, u, v):
    """Check (LB) after inserting edge (u,v).

    Adding edge (u,v) can only create new violations where the new edge
    serves as the 'ac' edge in the (LB) property:
      for positions a < b < c with ac in E (new) and ab not in E,
      need d < a with db in E and dc not in E.

    So we only check triples where {a,c} = {u,v}:
      Case 1: a=u, c=v (pos[u] < pos[v])
      Case 2: a=v, c=u (pos[v] < pos[u])
    For each, b ranges over positions between a and c.
    This is O(n) instead of O(n^2).
    """
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    pu = pos[u]
    pv = pos[v]

    # Case 1: a=u, c=v, requires pu < pv
    if pu < pv:
        for pb in range(pu + 1, pv):
            b = order[pb]
            # ab not in E?
            if adj[u] & (1 << b):
                continue  # ab in E, no violation possible
            # ac in E: yes, we just added (u,v)
            # Need: exists d < a=u with db in E and dc not in E
            W = adj[b] & ~adj[v]
            if not (W & prefix[pu]):
                return False

    # Case 2: a=v, c=u, requires pv < pu
    if pv < pu:
        for pb in range(pv + 1, pu):
            b = order[pb]
            if adj[v] & (1 << b):
                continue
            W = adj[b] & ~adj[u]
            if not (W & prefix[pv]):
                return False

    return True


def init(graph):
    n = len(graph)
    adj = _bitsets(graph)
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    adj = state['adj']
    adj[u] |= 1 << v
    adj[v] |= 1 << u
    order = state['ordering']
    if _check_lb_insert(adj, n, order, u, v):
        return {'ordering': order, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    adj = state['adj']
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    order = state['ordering']
    if _check_lb_full(adj, n, order):
        return {'ordering': order, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}
