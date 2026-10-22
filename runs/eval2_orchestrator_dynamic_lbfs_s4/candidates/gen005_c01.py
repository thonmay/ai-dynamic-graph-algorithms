"""Dynamic LexBFS ordering (candidate gen005_c01).

Strategy:
- init: static partition-refinement LexBFS (HMPV), deterministic tie-break.
- insert_edge / delete_edge: verify the existing ordering against the
  (LB) 4-point property of Corneil & Krueger using bitmasks; if still
  valid, keep it (no recompute).  Otherwise recompute from scratch.

Improvement over parent (gen002_c03): the verification loop is restructured
so that the expensive per-(a, c) work is done only when the pair (a, c) is
actually "active", i.e. ac in E and there exists some b in (a, c) with
ab not in E.  For inactive pairs we only pay O(1) bit tests.  This makes
verification cheap on dense graphs (where most pairs are active but the
inner b-loop is short) and on sparse graphs (where most pairs are
inactive).  The adjacency bitmasks are still cached in the state and
updated incrementally (only the two rows of the flipped edge are
rebuilt), so no full matrix re-scan is needed after an update.

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

    Uses bitmasks.  For each pair (a, c) with ac in E, we first test
    whether there is any b in (a, c) with ab not in E (one bit test);
    only then do we build the witness set S and scan b.
    """
    n = len(ordering)
    # prefix_mask[k] = bitmask of vertices at positions 0..k-1
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])

    for c in range(n):
        vc = ordering[c]
        adj_vc = adj_mask[vc]
        for a in range(c):
            va = ordering[a]
            if not (adj_vc >> va) & 1:
                continue  # ac not in E
            adj_va = adj_mask[va]
            # Is there any b in (a, c) with ab not in E?
            # If not, the pair (a, c) imposes no constraint.
            mid = prefix_mask[c] & ~prefix_mask[a + 1]
            if (adj_va & mid) == mid:
                continue  # va adjacent to every b in (a, c)
            # S = {d < a : dc not in E}
            S = prefix_mask[a] & ~adj_vc
            if S == 0:
                # No witness possible; any b with ab not in E fails
                for b in range(a + 1, c):
                    vb = ordering[b]
                    if not (adj_va >> vb) & 1:
                        return False
                continue
            for b in range(a + 1, c):
                vb = ordering[b]
                if (adj_va >> vb) & 1:
                    continue  # ab in E, no constraint
                # Need some d in S with db in E
                if (adj_mask[vb] & S) == 0:
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
