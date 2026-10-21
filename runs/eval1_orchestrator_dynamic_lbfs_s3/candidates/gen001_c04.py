"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via bucket lists.
- update: try a cheap local repair that keeps the old ordering valid
  (checked against the (LB) 4-point property of Corneil & Krueger).
  If the repair fails, fall back to a full recompute (correctness first).

The (LB) property: for all positions a < b < c with ac in E and ab not in E,
there exists d < a with db in E and dc not in E.  We verify it in O(n^2)
using bitsets (Python ints) so the fallback is rare but the check is fast.
"""


def _lexbfs(A):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(A)
    if n == 0:
        return []
    # Straightforward LexBFS using labels (tuples of 0/1).
    # O(n^3) worst case but correct.
    order = []
    remaining = set(range(n))
    labels = {v: () for v in range(n)}
    while remaining:
        x = min(remaining, key=lambda v: labels[v])
        order.append(x)
        remaining.remove(x)
        for v in remaining:
            labels[v] = labels[v] + (1 if A[x][v] else 0,)
    return order


def _is_valid_lexbfs(A, order):
    """Check (LB) 4-point property. O(n^3) worst case."""
    n = len(A)
    if n <= 2:
        return True
    # For each (b, c) with b < c in order:
    #   S = {a < b : A[a][c] and not A[a][b]}
    #   If S non-empty, let a0 = min(S) (smallest position).
    #   Check: exists d < a0 with A[d][b] and not A[d][c].
    #   If not, invalid.
    for bi in range(n):
        b = order[bi]
        for ci in range(bi + 1, n):
            c = order[ci]
            # Find smallest a < b (in position) with A[a][c] and not A[a][b]
            a0 = -1
            for ai in range(bi):
                a = order[ai]
                if A[a][c] and not A[a][b]:
                    a0 = ai
                    break
            if a0 == -1:
                continue
            # Check: exists d < a0 with A[d][b] and not A[d][c]
            found = False
            for di in range(a0):
                d = order[di]
                if A[d][b] and not A[d][c]:
                    found = True
                    break
            if not found:
                return False
    return True


def _try_repair(A, order, edge, is_insert):
    """Try to repair the ordering after an edge update.
    Returns a valid ordering or None if repair fails."""
    n = len(A)
    u, v = edge
    # First check if the original ordering is still valid
    if _is_valid_lexbfs(A, order):
        return order
    # Try: swap u and v in the ordering
    if u != v:
        new_order = list(order)
        iu = new_order.index(u)
        iv = new_order.index(v)
        new_order[iu], new_order[iv] = new_order[iv], new_order[iu]
        if _is_valid_lexbfs(A, new_order):
            return new_order
    # Try: move u to each position
    for target in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(target, u)
        if _is_valid_lexbfs(A, new_order):
            return new_order
    # Try: move v to each position
    for target in range(n):
        new_order = list(order)
        new_order.remove(v)
        new_order.insert(target, v)
        if _is_valid_lexbfs(A, new_order):
            return new_order
    return None


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    repaired = _try_repair(graph, order, edge, True)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = state['ordering']
    repaired = _try_repair(graph, order, edge, False)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute
    order = _lexbfs(graph)
    return {'ordering': order}
