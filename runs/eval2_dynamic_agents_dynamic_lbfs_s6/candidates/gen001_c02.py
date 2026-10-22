"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each edge update, try to
repair the existing ordering locally; if the repair fails, fall back to a
full O(n^2) partition-refinement LexBFS recompute.

Repair idea:
  - Insertion (u,v): the ordering may or may not still be valid.
  - Deletion (u,v): removing an edge can only make the (LB) property
    harder to satisfy (fewer witnesses d).
  In both cases, verify the (LB) 4-point property on the new graph;
  if it holds, keep the ordering. Otherwise recompute.

The (LB) property check uses bitsets for efficiency.
Fallback recompute: standard partition-refinement LexBFS in O(n^2) using
bitsets.
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
        # find first non-empty bucket
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break
        B = buckets[bi]
        # pick a vertex from B (lowest index for determinism)
        v = (B & -B).bit_length() - 1
        Bv = 1 << v
        B &= ~Bv
        remaining &= ~Bv
        order.append(v)

        Nv = adj[v]
        # refine: for each bucket, split into (bucket & Nv) and (bucket & ~Nv)
        new_buckets = []
        for i, C in enumerate(buckets):
            if i == bi:
                C = B  # already had v removed
            Cn = C & Nv
            Cnot = C & ~Nv
            if Cn:
                new_buckets.append(Cn)
            if Cnot:
                new_buckets.append(Cnot)
        buckets = new_buckets

    return order


def _check_lb(adj, n, order):
    """Check the (LB) 4-point property.

    For all positions a < b < c in the ordering with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True if valid.
    """
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    # prefix[i] = bitset of first i vertices in order
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    for pb in range(n):
        b = order[pb]
        for pc in range(pb + 1, n):
            c = order[pc]
            # A = {a : pa < pb, a not adj b, a adj c}
            A = prefix[pb] & ~adj[b] & adj[c]
            if not A:
                continue
            # W = {d : d adj b, d not adj c}
            W = adj[b] & ~adj[c]
            if not W:
                return False
            # Find min position in A
            min_pa = n
            tmp = A
            while tmp:
                lb = tmp & -tmp
                a = lb.bit_length() - 1
                pa = pos[a]
                if pa < min_pa:
                    min_pa = pa
                tmp ^= lb
            if not (W & prefix[min_pa]):
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
    if _check_lb(adj, n, order):
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
    if _check_lb(adj, n, order):
        return {'ordering': order, 'adj': adj, 'n': n}
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}
