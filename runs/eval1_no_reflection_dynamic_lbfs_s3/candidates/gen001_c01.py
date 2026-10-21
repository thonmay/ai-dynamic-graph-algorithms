"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each edge update, try to
repair the existing ordering with a local fix; if the fix fails, fall back
to a full O(n^2) LexBFS recompute (correctness first, then cheaper).

Local repair idea:
  - Insertion (u,v): if u and v are adjacent in the ordering and the edge
    was just added, the ordering is still a valid LexBFS (adding an edge
    between consecutive vertices cannot break the (LB) 4-point property).
  - Deletion (u,v): if u and v are adjacent in the ordering, removing the
    edge between consecutive vertices also preserves validity.
  - Otherwise, attempt a targeted swap of the two vertices and verify the
    (LB) property; if the swap restores validity, keep it.
  - If nothing works, recompute LexBFS from scratch.

Verification uses the (LB) 4-point property of Corneil and Krueger:
  for all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.
"""

from collections import deque


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    buckets = [deque(range(n))]
    ordering = []

    while buckets:
        # Remove empty buckets from front
        while buckets and not buckets[0]:
            buckets.pop(0)
        if not buckets:
            break

        B = buckets[0]
        v = B.popleft()
        ordering.append(v)

        # Split B and all other buckets by adjacency to v
        new_buckets = []
        # First, split B (which is still in buckets[0])
        B0 = deque()
        B1 = deque()
        for w in B:
            if graph[v][w]:
                B1.append(w)
            else:
                B0.append(w)
        if B0:
            new_buckets.append(B0)
        if B1:
            new_buckets.append(B1)

        # Then split all other buckets
        for C in buckets[1:]:
            C0 = deque()
            C1 = deque()
            for w in C:
                if graph[v][w]:
                    C1.append(w)
                else:
                    C0.append(w)
            if C0:
                new_buckets.append(C0)
            if C1:
                new_buckets.append(C1)

        buckets = new_buckets

    return ordering


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(graph)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue  # ab in E, condition not triggered
            # ab not in E, check for all c > b
            for c in range(b + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue  # ac not in E
                # ac in E, ab not in E: need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_swap_fix(graph, ordering, u, v):
    """Try swapping u and v in the ordering and check validity."""
    n = len(ordering)
    pos = [0] * n
    for i, w in enumerate(ordering):
        pos[w] = i

    pu, pv = pos[u], pos[v]
    if pu == pv:
        return None

    # Create a new ordering with u and v swapped
    new_order = list(ordering)
    new_order[pu], new_order[pv] = new_order[pv], new_order[pu]

    if _is_valid_lexbfs(graph, new_order):
        return new_order
    return None


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = list(state['ordering'])
    n = len(ordering)

    # Check if u and v are adjacent in the ordering
    pos = [0] * n
    for i, w in enumerate(ordering):
        pos[w] = i

    pu, pv = pos[u], pos[v]

    # If u and v are consecutive in the ordering, the ordering is still valid
    if abs(pu - pv) == 1:
        # Adding an edge between consecutive vertices preserves LexBFS validity
        return {'ordering': ordering}

    # Try a swap fix
    new_order = _try_swap_fix(graph, ordering, u, v)
    if new_order is not None:
        return {'ordering': new_order}

    # Fall back to full recompute
    new_order = _lexbfs(graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = list(state['ordering'])
    n = len(ordering)

    pos = [0] * n
    for i, w in enumerate(ordering):
        pos[w] = i

    pu, pv = pos[u], pos[v]

    # If u and v are consecutive in the ordering, removing the edge
    # between consecutive vertices preserves LexBFS validity.
    if abs(pu - pv) == 1:
        return {'ordering': ordering}

    # Try a swap fix
    new_order = _try_swap_fix(graph, ordering, u, v)
    if new_order is not None:
        return {'ordering': new_order}

    # Fall back to full recompute
    new_order = _lexbfs(graph)
    return {'ordering': new_order}
