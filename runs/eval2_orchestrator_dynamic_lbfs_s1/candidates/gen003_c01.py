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
        #   1. B's N(u)-part first,
        #   2. then the N(u)-parts of the other buckets in their old order,
        #   3. then B's non-N(u)-part,
        #   4. then the non-N(u)-parts of the other buckets in their old order.
        other_buckets = list(Q)
        Q.clear()

        def split(bucket):
            n_part = [v for v in bucket if graph[u][v]]
            nonn_part = [v for v in bucket if not graph[u][v]]
            return n_part, nonn_part

        B_n, B_nonn = split(B)
        if B_n:
            Q.append(B_n)
        for bucket in other_buckets:
            n_part, _ = split(bucket)
            if n_part:
                Q.append(n_part)
        if B_nonn:
            Q.append(B_nonn)
        for bucket in other_buckets:
            _, nonn_part = split(bucket)
            if nonn_part:
                Q.append(nonn_part)

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
    repaired = _try_repair_both(ordering, graph, u, v)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def _try_repair_both(ordering, graph, u, v):
    """Try moving u and/or v to new positions (independently, then jointly).

    Returns a repaired ordering if it passes the (LB) certificate, else None.
    """
    n = len(ordering)
    if n == 0:
        return ordering

    pu = ordering.index(u)
    pv = ordering.index(v)

    # Independent moves: move u (v stays), then move v (u stays).
    for vertex, pos in ((u, pu), (v, pv)):
        base = ordering[:pos] + ordering[pos + 1:]
        for new_pos in range(n):
            candidate = base[:new_pos] + [vertex] + base[new_pos:]
            if _is_valid_lexbfs(candidate, graph):
                return candidate

    # Joint moves: remove both, try all (new_u, new_v) position pairs.
    if pu < pv:
        base = ordering[:pu] + ordering[pu + 1:pv] + ordering[pv + 1:]
    else:
        base = ordering[:pv] + ordering[pv + 1:pu] + ordering[pu + 1:]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            candidate = base[:i] + [u] + base[i:j] + [v] + base[j:]
            if _is_valid_lexbfs(candidate, graph):
                return candidate
            candidate = base[:i] + [v] + base[i:j] + [u] + base[j:]
            if _is_valid_lexbfs(candidate, graph):
                return candidate
    return None


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']

    # Try local repair for both endpoints
    repaired = _try_repair_both(ordering, graph, u, v)
    if repaired is not None:
        return {'ordering': repaired}

    # Fallback: full recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
