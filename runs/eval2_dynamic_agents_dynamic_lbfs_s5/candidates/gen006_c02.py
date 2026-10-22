"""Dynamic LexBFS ordering (candidate gen006_c02).

Strategy: maintain a valid LexBFS ordering under single edge flips.

Correctness core:
  * init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
    with a deterministic tie-break (smallest vertex id first).
  * insert_edge: adding an edge can create a NEW 4-point violation (the new
    edge (a,c) can trigger the antecedent "ac in E and ab not in E" for a
    triple that was previously vacuously satisfied).  So we verify the (LB)
    property in O(n^2) using the current ordering; if it still holds we keep
    the ordering, otherwise we recompute.
  * delete_edge: removing an edge can break the 4-point property, so we
    verify the (LB) property in O(n^2) using the current ordering; if it
    still holds we keep the ordering, otherwise we recompute.

The state carries the ordering.  All work is done in pure Python with lists.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list.

    Correct HMPV algorithm:
      * P is an ordered list of buckets (each a list of vertices).
      * S is the set of already-output vertices.
      * At each step, pick the FIRST non-empty bucket, take its FIRST
        vertex v, output it, then refine every bucket by adjacency to v.
      * Refinement: for each bucket B, split into B_adj (neighbors of v)
        and B_nonadj (non-neighbors of v).  The refined bucket list is
        formed by replacing each B with [B_adj, B_nonadj] (in that order),
        dropping empty parts.  This preserves the lexicographic order of
        the neighbor-sets of S.
    """
    n = len(graph)
    if n == 0:
        return []
    # P: ordered list of buckets; each bucket is a list of vertices.
    P = [list(range(n))]
    S = set()
    order = []

    while len(S) < n:
        # find first non-empty bucket
        idx = None
        for i, B in enumerate(P):
            if B:
                idx = i
                break
        if idx is None:
            break
        B = P[idx]
        v = B[0]
        order.append(v)
        S.add(v)
        # remove v from its bucket
        B.pop(0)
        # refine: replace each bucket with [adj, nonadj]
        new_P = []
        for Bk in P:
            if not Bk:
                continue
            adj = []
            nonadj = []
            for x in Bk:
                if graph[x][v]:
                    adj.append(x)
                else:
                    nonadj.append(x)
            if adj:
                new_P.append(adj)
            if nonadj:
                new_P.append(nonadj)
        P = new_P
    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property: for all positions i < j < k with
    order[i]-order[k] in E and order[i]-order[j] not in E, there exists
    t < i with order[t]-order[j] in E and order[t]-order[k] not in E.
    Returns True if valid."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > b with ac in E
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue
                # need d < a (position) with db in E and dc not in E
                found = False
                for t in range(i):
                    d = order[t]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    return {
        'ordering': order,
        'n': n,
    }


def insert_edge(graph, edge, state):
    order = state['ordering']
    # Adding an edge CAN invalidate a LexBFS ordering: the new edge (a,c)
    # can create a new 4-point violation where the antecedent "ac in E and
    # ab not in E" was previously vacuously satisfied (ac was not in E).
    # Verify the (LB) property in O(n^2); if still valid, keep; else recompute.
    if _is_valid_lexbfs(graph, order):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }


def delete_edge(graph, edge, state):
    order = state['ordering']
    # Removing an edge can break the 4-point property.
    # Verify in O(n^2); if still valid, keep; else recompute.
    if _is_valid_lexbfs(graph, order):
        return {
            'ordering': order,
            'n': state['n'],
        }
    # recompute
    new_order = _lexbfs(graph)
    return {
        'ordering': new_order,
        'n': state['n'],
    }
