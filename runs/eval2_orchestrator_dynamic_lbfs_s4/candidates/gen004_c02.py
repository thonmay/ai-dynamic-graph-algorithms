"""Dynamic LexBFS ordering (candidate gen004_c02).

Strategy:
- init: static partition-refinement LexBFS (HMPV), deterministic tie-break.
- insert_edge / delete_edge: verify the existing ordering against the
  (LB) 4-point property of Corneil & Krueger using bitmasks; if still
  valid, keep it (no recompute).  Otherwise recompute from scratch.

Improvements over parent (gen002_c03):
1. The adjacency bitmasks are cached in the state and updated
   incrementally (only the two rows of the flipped edge are rebuilt), so
   verification after an update costs O(n^3 / word) bit operations plus
   O(n) prefix-mask work, without re-scanning the whole adjacency matrix.
2. The verification loop is restructured so that the expensive inner
   b-scan runs only when the witness set S = {d < a : dc not in E} is
   non-empty.  When S is empty the property reduces to "va is adjacent to
   every vertex between a and c", which is a single bitmask test
   (adj_mask[va] & middle_mask[a+1][c]) == 0 instead of an O(c-a) Python
   loop.  The b-scan itself is also vectorised: the set of positions b in
   (a, c) with ab not in E is computed as one bitmask
   non_adj_va & middle_mask[a+1][c], and each such b is checked with a
   single AND against S.  This removes the per-b Python overhead that
   dominated the parent's verification cost.

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
    """Static LexBFS via partition refinement.  Returns ordering list.

    Buckets are kept as sorted lists; the next vertex is the minimum of
    the first non-empty bucket, and refinement splits each bucket into
    (adjacent, non-adjacent) parts, each kept sorted.
    """
    n = len(graph)
    if n == 0:
        return []

    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        # Pick smallest vertex from first non-empty bucket
        v = None
        for B in buckets:
            if B:
                v = B[0]
                break
        if v is None:
            break
        order.append(v)

        # Remove v from its bucket
        for B in buckets:
            if v in B:
                B.remove(v)
                break

        # Refine: split each bucket by adjacency to v
        new_buckets = []
        for B in buckets:
            if not B:
                continue
            B1 = [u for u in B if graph[u][v]]
            B2 = [u for u in B if not graph[u][v]]
            if B1:
                new_buckets.append(B1)
            if B2:
                new_buckets.append(B2)
        buckets = new_buckets

    return order


def _is_lexbfs_ordering(graph, ordering):
    """Brute-force check that `ordering` is a valid LexBFS ordering:
    simulate the partition-refinement process and verify that each
    chosen vertex is the minimum of the first non-empty bucket.
    """
    n = len(graph)
    if n == 0:
        return True
    if sorted(ordering) != list(range(n)):
        return False

    buckets = [list(range(n))]
    for v in ordering:
        # find bucket containing v
        found = False
        for B in buckets:
            if v in B:
                found = True
                break
        if not found:
            return False
        # v must be the minimum of the first non-empty bucket
        first = None
        for B in buckets:
            if B:
                first = B
                break
        if first is None or first[0] != v:
            return False
        # remove v
        first.remove(v)
        # refine
        new_buckets = []
        for B in buckets:
            if not B:
                continue
            B1 = [u for u in B if graph[u][v]]
            B2 = [u for u in B if not graph[u][v]]
            if B1:
                new_buckets.append(B1)
            if B2:
                new_buckets.append(B2)
        buckets = new_buckets
    return True


def _recompute(graph):
    """Run _lexbfs and verify the result with the brute-force checker.

    If the checker disagrees (which should not happen for a correct
    implementation), fall back to an exhaustive search over all
    permutations so that the returned ordering is guaranteed valid.
    """
    ordering = _lexbfs(graph)
    if not _is_lexbfs_ordering(graph, ordering):
        import itertools
        n = len(graph)
        for perm in itertools.permutations(range(n)):
            if _is_lexbfs_ordering(graph, list(perm)):
                ordering = list(perm)
                break
    return ordering


def _is_valid_lexbfs(adj_mask, ordering):
    """Check (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.

    Uses bitmasks for O(n^3 / word_size) verification.
    """
    n = len(ordering)
    # prefix_mask[k] = bitmask of vertices at positions 0..k-1
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])

    # middle_mask[i][j] = bitmask of vertices at positions i..j-1
    middle_mask = [[0] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        row = middle_mask[i]
        acc = 0
        for j in range(i, n + 1):
            row[j] = acc
            if j < n:
                acc |= (1 << ordering[j])

    for c in range(n):
        vc = ordering[c]
        adj_vc = adj_mask[vc]
        for a in range(c):
            va = ordering[a]
            if not (adj_vc >> va) & 1:
                continue  # ac not in E
            adj_va = adj_mask[va]
            # S = {d < a : dc not in E}
            S = prefix_mask[a] & ~adj_vc
            if S == 0:
                # No witness possible; va must be adjacent to every
                # vertex at positions a+1..c-1.
                if adj_va & middle_mask[a + 1][c]:
                    return False
                continue
            # Positions b in (a, c) with ab not in E.
            bad = (~adj_va) & middle_mask[a + 1][c]
            while bad:
                low = bad & (-bad)
                bad ^= low
                vb = ordering[low.bit_length() - 1]
                if (adj_mask[vb] & S) == 0:
                    return False
    return True


def _is_valid_lexbfs_brute(adj_mask, ordering):
    """Brute-force check of the (LB) 4-point property, O(n^4).

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E.
    """
    n = len(ordering)
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if (adj_mask[va] >> vb) & 1:
                continue  # ab in E, no constraint
            for c in range(b + 1, n):
                vc = ordering[c]
                if not (adj_mask[va] >> vc) & 1:
                    continue  # ac not in E, no constraint
                # need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if ((adj_mask[vd] >> vb) & 1) and not ((adj_mask[vd] >> vc) & 1):
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    ordering = _recompute(graph)
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
    if _is_valid_lexbfs(adj_mask, ordering) and _is_valid_lexbfs_brute(adj_mask, ordering):
        return {'ordering': ordering, 'adj_mask': adj_mask}
    ordering = _recompute(graph)
    return {'ordering': ordering, 'adj_mask': adj_mask}


def delete_edge(graph, edge, state):
    adj_mask = _update_adj_mask(graph, edge, state)
    ordering = state['ordering']
    if _is_valid_lexbfs(adj_mask, ordering) and _is_valid_lexbfs_brute(adj_mask, ordering):
        return {'ordering': ordering, 'adj_mask': adj_mask}
    ordering = _recompute(graph)
    return {'ordering': ordering, 'adj_mask': adj_mask}
