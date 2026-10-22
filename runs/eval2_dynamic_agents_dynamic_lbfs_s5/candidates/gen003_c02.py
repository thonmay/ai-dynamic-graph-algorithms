"""Dynamic LexBFS ordering (candidate gen003_c02).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

- init: static LexBFS via label-based selection with proper signature
  comparison (0/1 vectors), O(n^2) with adjacency-matrix representation.
- insert_edge: try a local "repair" that keeps the current ordering if it
  remains a valid LexBFS; otherwise recompute.
- delete_edge: try a local repair; otherwise recompute.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < c with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static LexBFS via label-based selection.

    At each step, pick the unoutput vertex with lexicographically largest
    signature (0/1 vector of adjacency to output vertices in output order).
    Ties broken by vertex ID (smallest id wins).

    Returns the ordering list.
    """
    n = len(graph)
    if n == 0:
        return []

    unoutput = set(range(n))
    order = []
    # sigs[v] = list of 0/1, one entry per output vertex so far
    sigs = {v: [] for v in range(n)}

    for _ in range(n):
        # Pick vertex with lexicographically largest signature
        best = None
        best_sig = None
        for v in unoutput:
            if best is None:
                best = v
                best_sig = sigs[v]
            else:
                sv = sigs[v]
                if sv > best_sig:
                    best = v
                    best_sig = sv
                elif sv == best_sig and v < best:
                    best = v
                    best_sig = sv
        order.append(best)
        unoutput.remove(best)
        # Update signatures: append 1 if adjacent to best, else 0
        for v in unoutput:
            sigs[v].append(1 if graph[v][best] else 0)

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c (in the ordering) with
      ac in E and ab not in E,
    there exists d < c with db in E and dc not in E.

    Returns True if valid.
    """
    n = len(ordering)
    adj = graph
    for i in range(n):
        a = ordering[i]
        for j in range(i + 1, n):
            b = ordering[j]
            if adj[a][b]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > j
            for k in range(j + 1, n):
                c = ordering[k]
                if not adj[a][c]:
                    continue  # ac not in E, condition not triggered
                # ac in E, ab not in E: need d < k with db in E, dc not in E
                found = False
                for d_idx in range(k):
                    d = ordering[d_idx]
                    if adj[d][b] and not adj[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_repair_insert(graph, ordering, u, v):
    """After inserting edge (u,v), try to find a valid LexBFS ordering
    close to the current one. Returns a valid ordering or None."""
    n = len(ordering)
    # First check if the current ordering is still valid
    if _is_valid_lexbfs(graph, ordering):
        return ordering

    pos = {vertex: i for i, vertex in enumerate(ordering)}
    pu, pv = pos[u], pos[v]

    candidates = []
    # Try swapping u and v
    if pu != pv:
        cand = ordering[:]
        cand[pu], cand[pv] = cand[pv], cand[pu]
        candidates.append(cand)

    # Try moving u to position pv
    cand = ordering[:]
    x = cand.pop(pu)
    cand.insert(pv, x)
    candidates.append(cand)

    # Try moving v to position pu
    cand = ordering[:]
    x = cand.pop(pv)
    cand.insert(pu, x)
    candidates.append(cand)

    for cand in candidates:
        if _is_valid_lexbfs(graph, cand):
            return cand

    return None


def _try_repair_delete(graph, ordering, u, v):
    """After deleting edge (u,v), try to find a valid LexBFS ordering
    close to the current one. Returns a valid ordering or None."""
    n = len(ordering)
    if _is_valid_lexbfs(graph, ordering):
        return ordering

    pos = {vertex: i for i, vertex in enumerate(ordering)}
    pu, pv = pos[u], pos[v]

    candidates = []
    if pu != pv:
        cand = ordering[:]
        cand[pu], cand[pv] = cand[pv], cand[pu]
        candidates.append(cand)

    # Move u to pv
    cand = ordering[:]
    x = cand.pop(pu)
    cand.insert(pv, x)
    candidates.append(cand)

    # Move v to pu
    cand = ordering[:]
    x = cand.pop(pv)
    cand.insert(pu, x)
    candidates.append(cand)

    for cand in candidates:
        if _is_valid_lexbfs(graph, cand):
            return cand

    return None


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    repaired = _try_repair_insert(graph, ordering, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    repaired = _try_repair_delete(graph, ordering, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    # Fallback: full recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
