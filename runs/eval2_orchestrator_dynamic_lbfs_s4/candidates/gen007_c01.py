"""Dynamic LexBFS ordering (candidate gen007_c01).

Strategy:
- init: static partition-refinement LexBFS (HMPV), deterministic tie-break.
- insert_edge / delete_edge: verify the existing ordering against the
  (LB) 4-point property of Corneil & Krueger using bitmasks; if still
  valid, keep it (no recompute).  Otherwise recompute from scratch.

Improvement over parent (gen005_c01): the verification is restructured
from O(n^3) to O(n^2) bit operations.  For a fixed c, the property
requires that for every a < c with ac in E, every b in (a, c) with
ab not in E has a witness d < a with db in E and dc not in E.  We
process b in increasing order and maintain the bitmask U of a's that
are still "unwitnessed" (ac in E, a < b, and no earlier b' in (a, b)
had ab' not in E).  When b is processed, the a's that become
unwitnessed are exactly those in U that are not adjacent to b; each
such a must satisfy (adj[b] & S_a) != 0 where S_a = {d < a : dc not
in E}.  The check (adj[b] & S_a) != 0 for all a in a set T is
equivalent to (adj[b] & S_a) != 0 for the a in T with the smallest
S_a, since S_a is monotone non-decreasing in a (S_a = prefix[a] &
~adj[c] and prefix[a] grows with a).  So we only test the minimum
a in T.  Each a enters U at most once and leaves at most once per c,
giving O(n) bit ops per c and O(n^2) overall.

The adjacency bitmasks are cached in the state and updated
incrementally (only the two rows of the flipped edge are rebuilt), so
no full matrix re-scan is needed after an update.

Correctness: the 4-point property is a necessary and sufficient
condition for an ordering to be a LexBFS ordering, so verification is
exact.
"""


def _row_mask(row):
    mask = 0
    for j, bit in enumerate(row):
        if bit:
            mask |= (1 << j)
    return mask


def _adj_masks(graph):
    return [_row_mask(graph[i]) for i in range(len(graph))]


def _lexbfs(graph):
    """Static LexBFS via partition refinement.  Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets, forming a partition of remaining vertices
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # Pick smallest vertex from first non-empty bucket
        v = None
        for B in buckets:
            if B:
                v = min(B)
                break
        if v is None:
            break
        order.append(v)

        # Remove v from its bucket
        for B in buckets:
            if v in B:
                B.discard(v)
                break

        # Refine: split each bucket by adjacency to v
        new_buckets = []
        for B in buckets:
            if not B:
                continue
            B1 = set()
            B2 = set()
            for u in B:
                if graph[u][v]:
                    B1.add(u)
                else:
                    B2.add(u)
            if B1:
                new_buckets.append(B1)
            if B2:
                new_buckets.append(B2)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(adj_mask, ordering):
    """Check (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.

    O(n^2) bitmask algorithm.  See module docstring for the argument.
    """
    n = len(ordering)
    # prefix_mask[k] = bitmask of vertices at positions 0..k-1
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])

    for c in range(n):
        vc = ordering[c]
        adj_vc = adj_mask[vc]
        # U: bitmask of a's that are < current b, have ac in E, and have
        # not yet been "witnessed" by an earlier b' in (a, b) with
        # ab' not in E.
        U = 0
        for b in range(c):
            vb = ordering[b]
            adj_vb = adj_mask[vb]
            # a's that become unwitnessed at this b: in U, not adjacent
            # to b, and a < b (positions).
            T = U & ~adj_vb & prefix_mask[b]
            if T:
                # S_a = prefix_mask[a] & ~adj_vc is monotone non-decreasing
                # in a, so it suffices to check the smallest a in T.
                a = (T & -T).bit_length() - 1
                S = prefix_mask[a] & ~adj_vc
                if (adj_vb & S) == 0:
                    return False
            # a's that get witnessed at this b: in U and adjacent to b.
            U &= ~adj_vb
            # a's that become unwitnessed starting at this b: a == b-1
            # with ac in E (no b' in (a, b) exists yet).
            if (adj_vc >> vb) & 1:
                U |= (1 << vb)
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'adj_mask': _adj_masks(graph)}


def _update_adj_mask(graph, edge, state):
    """Return a fresh adj_mask list with the two rows of `edge` rebuilt."""
    u, v = edge
    adj_mask = state.get('adj_mask')
    if adj_mask is None or len(adj_mask) != len(graph):
        adj_mask = _adj_masks(graph)
    else:
        adj_mask = list(adj_mask)
    adj_mask[u] = _row_mask(graph[u])
    adj_mask[v] = _row_mask(graph[v])
    return adj_mask


def insert_edge(graph, edge, state):
    adj_mask = _update_adj_mask(graph, edge, state)
    ordering = state['ordering']
    if _is_valid_lexbfs(adj_mask, ordering):
        return {'ordering': ordering, 'adj_mask': adj_mask}
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'adj_mask': adj_mask}


def delete_edge(graph, edge, state):
    adj_mask = _update_adj_mask(graph, edge, state)
    ordering = state['ordering']
    if _is_valid_lexbfs(adj_mask, ordering):
        return {'ordering': ordering, 'adj_mask': adj_mask}
    ordering = _lexbfs(graph)
    return {'ordering': ordering, 'adj_mask': adj_mask}
