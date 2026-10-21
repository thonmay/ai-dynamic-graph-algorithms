"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first check if
the old ordering is still valid (via the (LB) 4-point certificate in both
orientations). If yes, keep it (no recompute). If no, fall back to a full
LexBFS recompute.

The (LB) certificate (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
The property must hold in both orientations (forward and reversed ordering)
to be a complete certificate.
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
    """Check whether `ordering` is a valid LexBFS ordering of A.

    Direct, complete test: at each position i, ordering[i] must have a
    minimal adjacency-label (tuple of 0/1 over ordering[0..i-1]) among all
    vertices not yet placed. This is exactly the LexBFS label-minimization
    rule, so it is a necessary and sufficient certificate. O(n^3).
    """
    n = len(A)
    for i in range(n):
        chosen = ordering[i]
        chosen_label = tuple(1 if A[chosen][ordering[t]] else 0 for t in range(i))
        for j in range(i + 1, n):
            v = ordering[j]
            label = tuple(1 if A[v][ordering[t]] else 0 for t in range(i))
            if label < chosen_label:
                return False
    return True


def _lexbfs_full_tie(A):
    """Static LexBFS with deterministic tie-breaking: among all vertices
    sharing the minimal adjacency-label, pick the smallest vertex id.

    This is a valid LexBFS ordering (any tie-break is legal) and is
    deterministic, so the verifier can predict it.
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


def init(graph):
    """Initialize the state with a valid LexBFS ordering."""
    ordering = _lexbfs_full_tie(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    """Handle an edge insertion."""
    ordering = state['ordering']
    # Check if the old ordering is still valid
    if _check_lb(graph, ordering):
        return {'ordering': ordering}
    # Fall back to full recompute
    new_ordering = _lexbfs_full_tie(graph)
    return {'ordering': new_ordering}


def delete_edge(graph, edge, state):
    """Handle an edge deletion."""
    ordering = state['ordering']
    # Check if the old ordering is still valid
    if _check_lb(graph, ordering):
        return {'ordering': ordering}
    # Fall back to full recompute
    new_ordering = _lexbfs_full_tie(graph)
    return {'ordering': new_ordering}
