"""Dynamic LexBFS ordering (candidate gen006_c01).

Strategy: maintain a valid LexBFS ordering under single edge flips.

Correctness core:
  * init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
    with a deterministic tie-break (smallest vertex id first).
  * insert_edge / delete_edge: a single edge flip (u,v) can only affect
    (LB) 4-point clauses in which the flipped edge participates.  We check
    exactly those clauses in O(n^2); if none is violated we keep the
    ordering, otherwise we recompute from scratch.

Why the targeted check is sufficient:
  The (LB) property is a conjunction over all triples (a,b,c) with
  positions a < b < c of:  [ac in E and ab not in E]  =>  exists d < a
  with db in E and dc not in E.
  Flipping edge (u,v) changes the truth value of a clause only if the
  flipped edge is one of the four edges the clause mentions: ac, ab, dc,
  or db.  All clauses not mentioning the flipped edge keep their truth
  value, and the ordering was valid before the flip, so they remain
  satisfied.  For each clause that does mention the flipped edge we
  re-evaluate it directly against the updated graph, so no direction
  (insert vs delete) is missed.

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


def _witness_exists(graph, order, pos, a, b, c):
    """Is there d at position t < pos[a] with db in E and dc not in E?"""
    for t in range(pos[a]):
        d = order[t]
        if graph[d][b] and not graph[d][c]:
            return True
    return False


def _clause_ok(graph, order, pos, a, b, c):
    """Evaluate one (LB) clause for the triple (a,b,c) (positions a<b<c):
    if ac in E and ab not in E, a witness d < a with db in E and
    dc not in E must exist."""
    if graph[a][c] and not graph[a][b]:
        return _witness_exists(graph, order, pos, a, b, c)
    return True


def _check_after_flip(graph, order, u, v):
    """Targeted (LB) check after flipping edge (u,v) (graph already
    updated).  Returns True iff the ordering is still a valid LexBFS
    ordering.  Only clauses mentioning the flipped edge can have changed
    status; every such clause is re-evaluated directly.

    A clause (a,b,c) mentions (u,v) iff one of its four edges ac, ab, dc,
    db equals (u,v).  This happens iff:
      * a is u or v (edges ac or ab), or
      * b is u or v (edges ab or db), or
      * c is u or v (edges ac or dc).
    We enumerate all triples (a,b,c) with positions a<b<c where at least
    one of a, b, c is u or v, and re-evaluate the clause.
    """
    n = len(order)
    pos = {vertex: i for i, vertex in enumerate(order)}
    pu, pv = pos[u], pos[v]

    for a in order:
        pa = pos[a]
        for b in order[pa + 1:]:
            pb = pos[b]
            for c in order[pb + 1:]:
                # clause mentions the flipped edge only if one of
                # a, b, c is u or v
                if (a != u and a != v and
                        b != u and b != v and
                        c != u and c != v):
                    continue
                if not _clause_ok(graph, order, pos, a, b, c):
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
    u, v = edge
    if _check_after_flip(graph, order, u, v):
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
    u, v = edge
    if _check_after_flip(graph, order, u, v):
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
