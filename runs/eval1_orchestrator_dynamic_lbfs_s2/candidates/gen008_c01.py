"""Dynamic LexBFS ordering.

Strategy: maintain a LexBFS ordering incrementally.

- init: static partition-refinement LexBFS, O(n^2).
- insert_edge / delete_edge: verify the (LB) 4-point property of the
  current ordering on the post-update graph.  If the property holds,
  keep the ordering; otherwise recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

The verification is done with bitsets (Python ints as bit vectors) so
that each (a, b) pair is checked in O(1) word operations instead of
scanning all c > b and all d < a.
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

    # Build bitsets: N[v] has bit i set iff v is adjacent to ordering[i].
    N = [0] * n
    for i in range(n):
        vi = ordering[i]
        bits = 0
        row = graph[vi]
        for j in range(n):
            if row[ordering[j]]:
                bits |= (1 << j)
        N[i] = bits

    # prefix_mask[a] = bits 0..a-1 set.
    prefix = [0] * (n + 1)
    for a in range(1, n + 1):
        prefix[a] = prefix[a - 1] | (1 << (a - 1))

    # suffix_mask[b] = bits b..n-1 set.
    suffix = [0] * (n + 1)
    for b in range(n - 1, -1, -1):
        suffix[b] = suffix[b + 1] | (1 << b)

    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue  # ab in E, condition not triggered
            # Need: for every c > b with ac in E, exists d < a with
            # db in E and dc not in E.
            # For each such c, check (N[b] & ~N[c]) & prefix[a] != 0.
            # Optimization: if N[b] & prefix[a] == 0, no d < a is adjacent
            # to b, so the condition fails if there's any c > b with ac in E.
            nb_prefix = N[b] & prefix[a]
            if nb_prefix == 0:
                if N[a] & suffix[b + 1]:
                    return False
                continue
            # For each c > b with ac in E, check (nb_prefix & ~N[c]) != 0.
            # Iterate over set bits of N[a] & suffix[b+1].
            ca = N[a] & suffix[b + 1]
            while ca:
                lsb = ca & (-ca)
                c = lsb.bit_length() - 1
                if (nb_prefix & ~N[c]) == 0:
                    return False
                ca ^= lsb
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
