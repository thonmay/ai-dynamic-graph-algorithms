"""Dynamic LexBFS ordering (candidate gen002_c04).

Strategy: maintain a valid LexBFS ordering under edge updates.

  * init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n^2) on the adjacency matrix.
  * insert_edge / delete_edge: check whether the OLD ordering is still a
    valid LexBFS ordering of the UPDATED graph via the (LB) 4-point
    property of Corneil and Krueger.  If it is, keep the state (no
    recompute).  If not, recompute a fresh LexBFS ordering.

The (LB) property: for all positions ia < ib < ic with
edge(order[ia], order[ic]) and not edge(order[ia], order[ib]), there
exists a position id < ia with edge(order[id], order[ib]) and
not edge(order[id], order[ic]).

The check is implemented with bitsets (Python ints as vertex masks) and
runs in O(n^2 / word) bit operations instead of O(n^4) scalar tests.
"""


def _lexbfs_ordering(adj, n):
    """Static LexBFS via partition refinement.

    adj: list of lists of 0/1 (current graph).
    Returns a list of n vertices in a valid LexBFS order.
    """
    if n == 0:
        return []
    # buckets: list of lists of vertices with the same label so far
    buckets = [[v] for v in range(n)]
    order = []

    while buckets:
        # pick the first vertex of the first bucket
        v = buckets[0].pop(0)
        if not buckets[0]:
            buckets.pop(0)
        order.append(v)
        # refine every remaining bucket by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = [x for x in b if adj[v][x]]
            nnb = [x for x in b if not adj[v][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(order, adj, n):
    """Check the (LB) 4-point property using bitsets.

    For all positions ia < ib < ic with edge(order[ia], order[ic]) and
    not edge(order[ia], order[ib]), there must exist a position id < ia
    with edge(order[id], order[ib]) and not edge(order[id], order[ic]).
    """
    if n == 0:
        return True

    # adj_mask[v] = bitset of neighbors of v
    adj_mask = [0] * n
    for v in range(n):
        m = 0
        row = adj[v]
        for u in range(n):
            if row[u]:
                m |= (1 << u)
        adj_mask[v] = m

    # prefix_mask[i] = bitset of vertices at positions < i
    prefix_mask = [0] * (n + 1)
    mask = 0
    for i, v in enumerate(order):
        prefix_mask[i] = mask
        mask |= (1 << v)
    prefix_mask[n] = mask

    # pos[v] = position of vertex v in the ordering
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i

    for ib in range(n):
        vb = order[ib]
        nb = adj_mask[vb]
        # candidate c's: positions after ib, adjacent to vb
        cs = nb & ~prefix_mask[ib + 1]
        while cs:
            c = (cs & -cs).bit_length() - 1
            cs &= cs - 1
            nc = adj_mask[c]
            # candidate a's: positions before ib, adjacent to c
            A = prefix_mask[ib] & nc
            while A:
                a = (A & -A).bit_length() - 1
                A &= A - 1
                if not (nb & (1 << a)):
                    # triggering triple (a, b, c): need witness d < a
                    if (nb & prefix_mask[pos[a]] & ~nc) == 0:
                        return False
    return True


def _is_valid_lexbfs_brute(order, adj, n):
    """Brute-force (LB) 4-point property check, O(n^4).

    For all positions ia < ib < ic with edge(order[ia], order[ic]) and
    not edge(order[ia], order[ib]), there must exist a position id < ia
    with edge(order[id], order[ib]) and not edge(order[id], order[ic]).
    """
    for ia in range(n):
        va = order[ia]
        for ib in range(ia + 1, n):
            vb = order[ib]
            if adj[va][vb]:
                continue
            for ic in range(ib + 1, n):
                vc = order[ic]
                if not adj[va][vc]:
                    continue
                found = False
                for id_ in range(ia):
                    vd = order[id_]
                    if adj[vd][vb] and not adj[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    order = _lexbfs_ordering(graph, n)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    if _is_valid_lexbfs(order, graph, n):
        return state
    order = _lexbfs_ordering(graph, n)
    return {'ordering': order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    if _is_valid_lexbfs(order, graph, n):
        return state
    order = _lexbfs_ordering(graph, n)
    return {'ordering': order, 'n': n}
