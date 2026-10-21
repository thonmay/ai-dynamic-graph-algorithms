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

    Bitset implementation: for each vertex v, N[v] is the set of
    vertices after v in the ordering that are adjacent to v.  A
    violation at (a, b, c) requires N[va] & ~N[vb] & ~N[vc] == 0.
    """
    n = len(ordering)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    N = [0] * n
    for i, v in enumerate(ordering):
        row = graph[v]
        mask = 0
        for j in range(i + 1, n):
            if row[ordering[j]]:
                mask |= 1 << j
        N[v] = mask

    for a in range(n):
        va = ordering[a]
        Na = N[va]
        for b in range(a + 1, n):
            vb = ordering[b]
            if Na & (1 << b):
                continue  # ab in E, condition not triggered
            # c > b with ac in E: candidates = Na & ~N[vb] & (bits > b)
            cands = Na & ~N[vb] & ~((1 << (b + 1)) - 1)
            while cands:
                c = (cands & -cands).bit_length() - 1
                if N[va] & N[ordering[c]] & ((1 << a) - 1):
                    cands &= cands - 1
                else:
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
