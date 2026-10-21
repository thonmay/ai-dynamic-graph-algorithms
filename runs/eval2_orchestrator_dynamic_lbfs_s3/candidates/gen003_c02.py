"""Dynamic LexBFS ordering (candidate gen003_c02).

Strategy: maintain a valid LexBFS ordering under edge updates.

Correctness core: after any update, if the current ordering is no longer a
valid LexBFS ordering of the new graph, recompute a fresh LexBFS ordering
from scratch (O(n^2) partition-refinement).  If it is still valid, keep it.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

The check iterates over ORDERING POSITIONS (not vertex ids) and uses
bitsets (Python ints as bit masks) for the witness test.
"""


def _lexbfs_ordering(adj, n):
    """Static LexBFS via partition refinement (Habib-McConnell-Paul-Viennot).

    adj: list of lists of 0/1 (current graph).
    Returns a list of n vertices in a valid LexBFS order.

    Refinement rule: within each bucket, vertices NOT adjacent to the
    chosen vertex come before those adjacent to it (the non-neighbor
    part carries the smaller label and sorts first).
    """
    buckets = [[v] for v in range(n)]
    order = []

    for _ in range(n):
        b = buckets[0]
        u = b.pop(0)
        order.append(u)
        if not b:
            buckets.pop(0)
        # refine: for each bucket, split by adjacency to u
        new_buckets = []
        for bk in buckets:
            if not bk:
                continue
            nb = [x for x in bk if adj[u][x]]
            nnb = [x for x in bk if not adj[u][x]]
            if nnb:
                new_buckets.append(nnb)
            if nb:
                new_buckets.append(nb)
        buckets = new_buckets
    return order


def _is_valid_lexbfs(order, adj, n):
    """Check the (LB) 4-point property over ordering positions.

    For all positions ia < ib < ic with edge(order[ia], order[ic]) and
    not edge(order[ia], order[ib]), there must exist a position id < ia
    with edge(order[id], order[ib]) and not edge(order[id], order[ic]).
    """
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
                # triggering triple: need witness d at position < ia
                found = False
                for id_ in range(ia):
                    vd = order[id_]
                    if adj[vd][vb] and not adj[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _is_valid_lexbfs_lex(order, adj, n):
    """Check that the ordering is a valid LexBFS ordering by comparing
    against a reference LexBFS ordering.

    Two orderings are both valid LexBFS orderings of the same graph iff
    they induce the same sequence of neighbor/non-neighbor partitions
    (i.e., the same "LexBFS signature").  We compute the signature of
    both orderings and compare.
    """
    ref = _lexbfs_ordering(adj, n)
    return _lexbfs_signature(order, adj, n) == _lexbfs_signature(ref, adj, n)


def _lexbfs_signature(order, adj, n):
    """Compute the LexBFS signature: for each vertex in order, the
    sequence of (neighbor, non-neighbor) partition labels of the
    remaining vertices.  Two orderings have the same signature iff
    they are both valid LexBFS orderings of the same graph.
    """
    # For each vertex v in order, record the set of vertices that
    # appear before v and are adjacent to v (as a frozenset).
    # The signature is the tuple of these sets in order.
    sig = []
    seen = set()
    for v in order:
        # neighbors of v that appear before v in the ordering
        pred_nb = frozenset(u for u in seen if adj[v][u])
        sig.append(pred_nb)
        seen.add(v)
    return tuple(sig)


def _is_valid_lexbfs_direct(order, adj, n):
    """Direct (LB) 4-point property check.

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
                # triggering triple: need witness d at position < ia
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
    # The graph parameter is the PRE-update matrix; apply the insertion
    # to a copy so validity checks and recomputation see the new graph.
    new_graph = [row[:] for row in graph]
    u, v = edge
    new_graph[u][v] = 1
    new_graph[v][u] = 1
    order = state['ordering']
    if _is_valid_lexbfs_direct(order, new_graph, n):
        return state
    order = _lexbfs_ordering(new_graph, n)
    return {'ordering': order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    # The graph parameter is the PRE-update matrix; apply the deletion
    # to a copy so validity checks and recomputation see the new graph.
    new_graph = [row[:] for row in graph]
    u, v = edge
    new_graph[u][v] = 0
    new_graph[v][u] = 0
    order = state['ordering']
    if _is_valid_lexbfs_direct(order, new_graph, n):
        return state
    order = _lexbfs_ordering(new_graph, n)
    return {'ordering': order, 'n': n}
