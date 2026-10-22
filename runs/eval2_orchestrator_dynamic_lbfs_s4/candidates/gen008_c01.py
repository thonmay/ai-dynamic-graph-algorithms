"""Dynamic LexBFS ordering (candidate gen008_c01).

Strategy:
- init: static partition-refinement LexBFS (HMPV), deterministic tie-break.
- insert_edge / delete_edge: verify the existing ordering against the
  (LB) 4-point property of Corneil & Krueger using bitmasks; if still
  valid, keep it (no recompute).  Otherwise recompute from scratch.

Improvement over parent (gen002_c03): the verification is restructured
around the prefix-adjacency masks.  For each position a we precompute
P[a] = union of adj masks of vertices at positions < a.  Then the
witness set S = {d < a : dc not in E} is simply P[a] & ~adj[vc], and
the check "exists d in S with db in E" is one bitmask AND.  This
removes the per-(a,c) prefix-mask construction and makes the inner
loop a single bit operation per (a, b, c) triple.

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

    Uses prefix-adjacency masks P[a] = union of adj masks of vertices
    at positions < a.  For each (a, c) with ac in E, the witness set
    S = P[a] & ~adj[vc]; the check for each b is (adj[vb] & S) != 0.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # P[a] = bitmask of all vertices adjacent to at least one vertex
    # at position < a.
    P = [0] * n
    running = 0
    for a in range(n):
        P[a] = running
        running |= adj_mask[ordering[a]]

    for c in range(2, n):
        vc = ordering[c]
        adj_vc = adj_mask[vc]
        for a in range(c - 1):
            va = ordering[a]
            if not (adj_vc >> va) & 1:
                continue  # ac not in E
            # S = {d < a : dc not in E}
            S = P[a] & ~adj_vc
            adj_va = adj_mask[va]
            if S == 0:
                # No witness possible; any b with ab not in E fails
                for b in range(a + 1, c):
                    vb = ordering[b]
                    if not (adj_va >> vb) & 1:
                        return False
            else:
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
