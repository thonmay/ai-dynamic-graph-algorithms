"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first check if
the old ordering is still valid (via the (LB) 4-point certificate). If yes,
keep it (no recompute). If no, fall back to a full LexBFS recompute.

The (LB) certificate: for all positions a < b < c with ac in E and ab not
in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs_full(A):
    """Static LexBFS via label minimization. O(n^3).

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(A)
    if n == 0:
        return []

    ordering = []
    remaining = set(range(n))
    while remaining:
        best = None
        best_label = None
        for v in sorted(remaining):
            label = tuple(1 if A[v][u] else 0 for u in ordering)
            if best_label is None or label < best_label:
                best_label = label
                best = v
        ordering.append(best)
        remaining.remove(best)
    return ordering


def _check_lb(A, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True if the ordering is a valid LexBFS ordering.
    """
    n = len(A)
    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if A[a][b]:
                continue  # ab in E, skip
            # For each c with pos[c] > pos[b] and A[a][c]:
            for k in range(j + 1, n):
                c = ordering[k]
                if not A[a][c]:
                    continue
                # Need d < a with A[d][b] and not A[d][c]
                found = False
                for l in range(i):
                    d = ordering[l]
                    if A[d][b] and not A[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle an edge insertion."""
    ordering = state['ordering']
    # Check if the old ordering is still valid
    if _check_lb(graph, ordering):
        return {'ordering': ordering}
    # Fall back to full recompute
    new_ordering = _lexbfs_full(graph)
    return {'ordering': new_ordering}


def delete_edge(graph, edge, state):
    """Handle an edge deletion."""
    ordering = state['ordering']
    # Check if the old ordering is still valid
    if _check_lb(graph, ordering):
        return {'ordering': ordering}
    # Fall back to full recompute
    new_ordering = _lexbfs_full(graph)
    return {'ordering': new_ordering}
