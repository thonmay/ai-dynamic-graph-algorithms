"""Dynamic LexBFS ordering (candidate gen006_c01).

Strategy:
- init: static partition-refinement LexBFS (HMPV), deterministic tie-break.
- insert_edge / delete_edge: verify the existing ordering against the
  (LB) 4-point property of Corneil & Krueger using bitmasks; if still
  valid, keep it (no recompute).  Otherwise recompute from scratch.

Improvement over parent (gen002_c03): the verification is restructured so
the per-(c, a) work is O(|S|) big-int ops plus one O(c - a) scan, instead
of O(c - a) Python iterations each doing a big-int AND.  For each (c, a)
with ac in E, S = {d < a : dc not in E}.  A b in (a, c) with ab not in E
is a violation iff adj[b] & S == 0, i.e. b lies in
    F = intersection over d in S of (~adj[d]).
F is computed incrementally over the (usually few) bits of S, and the
pair is a violation iff F intersects the mask B of b's in (a, c) with
ab not in E.  When S is empty the pair is a violation iff B is nonempty.

Correctness: the 4-point property is a necessary and sufficient condition
for an ordering to be a LexBFS ordering, so verification is exact.
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

    Bitmask verification.  For each (c, a) with ac in E:
      S = {d < a : dc not in E}
      If S is empty, every b in (a, c) with ab not in E is a violation.
      Otherwise, b is a violation iff adj[b] & S == 0.
    We collect the violating b's as a bitmask and test membership.
    """
    n = len(ordering)
    if n == 0:
        return True

    # prefix_mask[k] = bitmask of vertices at positions 0..k-1
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])
    ALL = (1 << n) - 1

    for c in range(n):
        vc = ordering[c]
        adj_vc = adj_mask[vc]
        for a in range(c):
            va = ordering[a]
            if not (adj_vc >> va) & 1:
                continue  # ac not in E
            # S = {d < a : dc not in E}
            S = prefix_mask[a] & ~adj_vc
            if S == 0:
                # Any b in (a, c) with ab not in E is a violation.
                adj_va = adj_mask[va]
                for b in range(a + 1, c):
                    if not (adj_va >> ordering[b]) & 1:
                        return False
                continue
            # b fails iff adj[b] & S == 0, i.e. b is in
            #   F = intersection over d in S of (~adj[d]).
            # Compute F incrementally over the (usually few) bits of S.
            F = ALL
            rem = S
            while rem:
                low = rem & (-rem)
                vd = low.bit_length() - 1
                F &= ~adj_mask[vd]
                if F == 0:
                    break
                rem ^= low
            if F == 0:
                continue
            # B = {b : a < pos(b) < c, ab not in E}; violation iff B & F.
            adj_va = adj_mask[va]
            B = 0
            for b in range(a + 1, c):
                vb = ordering[b]
                if not (adj_va >> vb) & 1:
                    B |= (1 << vb)
            if B & F:
                return False
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
