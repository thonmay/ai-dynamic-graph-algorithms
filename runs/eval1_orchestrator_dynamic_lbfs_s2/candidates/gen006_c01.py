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
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue  # ab in E, condition not triggered
            for c in range(b + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue  # ac not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
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
