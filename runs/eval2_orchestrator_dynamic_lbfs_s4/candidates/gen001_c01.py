"""Dynamic LexBFS ordering (candidate gen001_c01).

Maintains a valid LexBFS ordering under edge insertions/deletions.
On each update, tries cheap local repairs (moving endpoints to a few
positions); falls back to full static partition-refinement LexBFS.
Adjacency is kept as Python-int bitsets for fast validation.
"""


def _adj_bitsets(graph):
    n = len(graph)
    adj = [0] * n
    for i in range(n):
        row = graph[i]
        bits = 0
        for j in range(n):
            if row[j]:
                bits |= (1 << j)
        adj[i] = bits
    return adj


def _validate(order, adj):
    """Check the 4-point (LB) property of Corneil-Krueger.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    # pos_adj[x] = bitset of positions of neighbors of x
    pos_adj = [0] * n
    for v in range(n):
        bits = 0
        nb = adj[v]
        while nb:
            lsb = nb & (-nb)
            j = lsb.bit_length() - 1
            bits |= (1 << pos[j])
            nb ^= lsb
        pos_adj[v] = bits
    for pa in range(n):
        a = order[pa]
        a_nb = adj[a]
        mask_lt_pa = (1 << pa) - 1
        for pb in range(pa + 1, n):
            b = order[pb]
            if (a_nb >> b) & 1:
                continue  # ab in E, skip
            # For each pc > pb with ac in E, check witness
            mask_gt_pb = ~((1 << (pb + 1)) - 1)
            c_bits = pos_adj[a] & mask_gt_pb
            while c_bits:
                lsb = c_bits & (-c_bits)
                pc = lsb.bit_length() - 1
                c = order[pc]
                if (pos_adj[b] & mask_lt_pa & ~pos_adj[c]) == 0:
                    return False
                c_bits ^= lsb
    return True


def _lexbfs_full(adj):
    """Static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)."""
    n = len(adj)
    if n == 0:
        return []
    order = []
    # Partition: list of lists of unvisited vertices.
    # Initially one set with all vertices.
    partition = [[v for v in range(n)]]
    for _ in range(n):
        # Find first non-empty set, take its first element
        idx = 0
        while idx < len(partition) and not partition[idx]:
            partition.pop(idx)
        if idx >= len(partition):
            break
        v = partition[idx].pop(0)
        order.append(v)
        # Refine each set: split by adjacency to v
        new_partition = []
        for S in partition:
            if not S:
                continue
            S_adj = [x for x in S if (adj[v] >> x) & 1]
            S_non = [x for x in S if not ((adj[v] >> x) & 1)]
            if S_adj:
                new_partition.append(S_adj)
            if S_non:
                new_partition.append(S_non)
        partition = new_partition
    return order


def _try_repair(order, adj, u, v):
    """Try to repair the ordering after an edge update between u and v.
    Returns a valid ordering if found, else None."""
    n = len(order)
    # Try several candidate orderings: original, and variants where u and/or v
    # are moved to the front, to the back, or swapped.
    candidates = [list(order)]
    # u to front
    o = [x for x in order if x != u]
    o.insert(0, u)
    candidates.append(o)
    # v to front
    o = [x for x in order if x != v]
    o.insert(0, v)
    candidates.append(o)
    # both to front (u first)
    o = [x for x in order if x != u and x != v]
    o.insert(0, v)
    o.insert(0, u)
    candidates.append(o)
    # both to front (v first)
    o = [x for x in order if x != u and x != v]
    o.insert(0, u)
    o.insert(0, v)
    candidates.append(o)
    # u to back
    o = [x for x in order if x != u]
    o.append(u)
    candidates.append(o)
    # v to back
    o = [x for x in order if x != v]
    o.append(v)
    candidates.append(o)
    # swap u and v
    if u != v:
        o = list(order)
        pu = o.index(u)
        pv = o.index(v)
        o[pu], o[pv] = o[pv], o[pu]
        candidates.append(o)
    # u to position 1
    o = [x for x in order if x != u]
    o.insert(1, u)
    candidates.append(o)
    # v to position 1
    o = [x for x in order if x != v]
    o.insert(1, v)
    candidates.append(o)
    for cand in candidates:
        if _validate(cand, adj):
            return cand
    return None


def init(graph):
    adj = _adj_bitsets(graph)
    order = _lexbfs_full(adj)
    return {'adj': adj, 'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u] |= (1 << v)
    adj[v] |= (1 << u)
    order = state['ordering']
    new_order = _try_repair(order, adj, u, v)
    if new_order is None:
        new_order = _lexbfs_full(adj)
    return {'adj': adj, 'ordering': new_order}


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u] &= ~(1 << v)
    adj[v] &= ~(1 << u)
    order = state['ordering']
    new_order = _try_repair(order, adj, u, v)
    if new_order is None:
        new_order = _lexbfs_full(adj)
    return {'adj': adj, 'ordering': new_order}
