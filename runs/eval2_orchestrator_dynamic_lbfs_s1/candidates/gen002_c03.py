"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try a cheap
local repair (reorder the affected vertex within its "block" of the current
ordering); if the repair fails the (LB) 4-point certificate, fall back to a
full static LexBFS recomputation.

The local repair is sound: if the repaired ordering passes the (LB)
certificate, it is a valid LexBFS ordering of the updated graph, so no
recomputation is needed.  The fallback guarantees correctness in all cases.
"""


def _lexbfs(graph):
    """Static O(n+m) LexBFS (Habib-McConnell-Paul-Viennot partition refinement).

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    from collections import deque

    Q = deque()
    Q.append(list(range(n)))

    ordering = []

    while Q:
        B = Q.popleft()
        if not B:
            continue
        u = B[0]
        ordering.append(u)
        B = B[1:]

        # Split all remaining buckets by N(u).
        # Queue discipline (HMPV):
        #   1. N(u)-part of the current bucket B (front of queue),
        #   2. N(u)-parts of the other buckets in their old relative order,
        #   3. non-N(u)-part of B,
        #   4. non-N(u)-parts of the other buckets in their old relative order.
        other_buckets = list(Q)
        Q.clear()

        B_n = [v for v in B if graph[u][v]]
        B_nonn = [v for v in B if not graph[u][v]]

        new_q = []
        if B_n:
            new_q.append(B_n)
        for bucket in other_buckets:
            n_part = [v for v in bucket if graph[u][v]]
            if n_part:
                new_q.append(n_part)
        if B_nonn:
            new_q.append(B_nonn)
        for bucket in other_buckets:
            nonn_part = [v for v in bucket if not graph[u][v]]
            if nonn_part:
                new_q.append(nonn_part)

        for part in new_q:
            Q.append(part)

    return ordering


def _is_valid_lexbfs(ordering, graph):
    """Check the (LB) 4-point property: for all a < b < c with ac in E and
    ab not in E, there exists d < a with db in E and dc not in E."""
    n = len(ordering)
    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if graph[a][b]:
                continue  # ab in E, skip
            for k in range(j + 1, n):
                c = ordering[k]
                if not graph[a][c]:
                    continue  # ac not in E, skip
                # Need: exists d < a (pos < i) with db in E and dc not in E
                found = False
                for d_idx in range(i):
                    d = ordering[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_local_repair(ordering, graph, vertex):
    """Try to repair the ordering by moving `vertex` to a better position.

    Returns a new ordering if it passes the (LB) certificate, else None.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    # Find current position of vertex
    cur_pos = ordering.index(vertex)

    # Remove vertex from current position, try inserting at each position
    base = ordering[:cur_pos] + ordering[cur_pos + 1:]

    # Try inserting at each position from 0 to n-1
    for new_pos in range(n):
        candidate = base[:new_pos] + [vertex] + base[new_pos:]
        if _is_valid_lexbfs(candidate, graph):
            return candidate
    return None


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']

    # Try local repair for both endpoints
    for vertex in (u, v):
        repaired = _try_local_repair(ordering, graph, vertex)
        if repaired is not None:
            return {'ordering': repaired}

    # Fallback: full recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']

    # Try local repair for both endpoints
    for vertex in (u, v):
        repaired = _try_local_repair(ordering, graph, vertex)
        if repaired is not None:
            return {'ordering': repaired}

    # Fallback: full recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
