"""Dynamic LexBFS ordering.

Strategy: maintain a LexBFS ordering incrementally.

- init: static partition-refinement LexBFS, O(n^2).
- insert_edge / delete_edge: verify the (LB) 4-point property of the
  current ordering on the post-update graph.  If the property holds,
  keep the ordering; otherwise recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement.  Returns the ordering."""
    n = len(graph)
    if n == 0:
        return []

    # Partition: list of lists of unprocessed vertices.
    part = [list(range(n))]
    ordering = []

    for _ in range(n):
        # Find the first non-empty bucket.
        bi = None
        for i, b in enumerate(part):
            if b:
                bi = i
                break
        if bi is None:
            break

        # Take the first vertex in this bucket.
        v = part[bi][0]
        part[bi] = part[bi][1:]
        ordering.append(v)

        # Refine the partition by N(v): for each bucket, split into
        # (intersection with N(v), rest).  The intersection part goes
        # before the rest.
        new_part = []
        for b in part:
            if not b:
                continue
            inter = [x for x in b if graph[v][x]]
            rest = [x for x in b if not graph[v][x]]
            if inter:
                new_part.append(inter)
            if rest:
                new_part.append(rest)
        part = new_part

    return ordering


def _recompute(graph):
    """Recompute the LexBFS ordering from scratch."""
    return _lexbfs(graph)


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property for `ordering` on `graph`.

    For all positions a < b < c with ac in E and ab not in E, there
    exists d < a with db in E and dc not in E.

    Bitset implementation: for each vertex v, N[v] is the bitset of its
    neighbours.  For a fixed (a, b) with ab not in E, the set of
    witnesses d < a is (N[b] & ~N[c]) & prefix_mask[a]; the condition
    fails iff this is empty for every c > b with ac in E, i.e. iff
    (N[b] & ~N[a]) & prefix_mask[a] & suffix_mask[b+1] == 0.
    """
    n = len(ordering)
    if n == 0:
        return True

    # Bitset of neighbours of each vertex.
    N = [0] * n
    for v in range(n):
        row = graph[v]
        bits = 0
        for u in range(n):
            if row[u]:
                bits |= 1 << u
        N[v] = bits

    # prefix_mask[i] = bits 0..i-1 (positions before i).
    prefix_mask = [0] * (n + 1)
    for i in range(1, n + 1):
        prefix_mask[i] = prefix_mask[i - 1] | (1 << (i - 1))

    # suffix_mask[i] = bits i..n-1 (positions from i on).
    suffix_mask = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix_mask[i] = suffix_mask[i + 1] | (1 << i)

    for a in range(n):
        va = ordering[a]
        na = N[va]
        pm = prefix_mask[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if na >> vb & 1:
                continue  # ab in E, condition not triggered
            # For this (a,b), we need: for all c > b with ac in E,
            # there exists d < a with db in E and dc not in E.
            # Failure: exists c > b with ac in E and
            #   (N[b] & ~N[c]) & pm == 0
            # i.e., N[b] & pm is a subset of N[c] & pm.
            nb_pm = N[vb] & pm  # neighbours of b that are before a
            if nb_pm == 0:
                # No d < a is adjacent to b, so if there's any c > b
                # with ac in E, the property fails.
                if na & suffix_mask[b + 1]:
                    return False
                continue
            # For each c > b with ac in E, check if nb_pm & ~N[c] == 0.
            # Equivalently: nb_pm ⊆ N[c].
            c_mask = na & suffix_mask[b + 1]
            while c_mask:
                lb = c_mask & (-c_mask)
                c = lb.bit_length() - 1
                vc = ordering[c]
                if nb_pm & ~N[vc] == 0:
                    return False
                c_mask ^= lb
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle edge insertion.  Verify the ordering is still a valid
    LexBFS ordering on the post-update graph; recompute if not."""
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    return {'ordering': _recompute(graph)}


def delete_edge(graph, edge, state):
    """Handle edge deletion.  Verify the ordering is still a valid
    LexBFS ordering on the post-update graph; recompute if not."""
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    return {'ordering': _recompute(graph)}
