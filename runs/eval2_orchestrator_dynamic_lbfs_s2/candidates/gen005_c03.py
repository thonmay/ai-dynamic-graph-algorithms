"""Dynamic LexBFS ordering (candidate gen005_c03).

Strategy: maintain a valid LexBFS ordering in the state.  After each edge
update, first try to keep the old ordering: check the Corneil-Krueger
(LB) 4-point property exactly on the old ordering in the *new* graph.
If the old ordering is still a valid LexBFS ordering of the updated
graph, return it unchanged (no recompute).  Otherwise fall back to a
full static partition-refinement LexBFS recompute.

The verification is the *complete* (LB) property: for every triple of
positions a < b < c with ac in E and ab not in E, there must exist a
position d < a with db in E and dc not in E.  This is exactly the
certificate the verifier uses, so the fast path is sound: an ordering
that passes the check is a valid LexBFS ordering of the current graph.

The (LB) property is monotone under edge deletion (deleting an edge can
only create new violations, never destroy existing witnesses), so the
fast path is most useful for insertions; for deletions it is still tried
and simply falls back to recompute when the old ordering is invalid.

The check is implemented with bitsets: for positions b < c with bc in E,
let Bad = {a < b : ab not in E and ac in E} and W = {d : db in E and dc
not in E}.  The (LB) condition for (b, c) is: for every a in Bad, W has
a member below a, which (since W is fixed) holds iff the lowest member
of W is below the lowest member of Bad.
"""


def _is_lexbfs(graph, order):
    """Check the (LB) 4-point property of Corneil and Krueger exactly.

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E.
    """
    n = len(order)
    # adj_pos[i] = bitmask of positions j < i adjacent to order[i].
    adj_pos = [0] * n
    for i in range(n):
        v = order[i]
        row = graph[v]
        mask = 0
        for j in range(i):
            if row[order[j]]:
                mask |= (1 << j)
        adj_pos[i] = mask

    # For each pair b < c with bc in E, the (LB) condition is:
    #   for all a < b with ab not in E and ac in E:
    #     exists d < a with db in E and dc not in E.
    #
    # For fixed (b, c), let W = {d < b : db in E and dc not in E}
    # (witnesses must be < a <= b, so restricting to d < b is exact).
    # For each a < b, the witness condition is: W has a member < a,
    # i.e. min(W) < a.  The "bad" a's are those with ab not in E and
    # ac in E.  So the condition for (b, c) is:
    #   for all a in Bad = {a < b : ab not in E and ac in E}: min(W) < a.
    #
    # A bad a is unwitnessed iff a <= min(W) (no witness strictly below
    # a).  So the condition is: no bad a lies in [0, min(W)], i.e.
    #   Bad & ((1 << (minW + 1)) - 1) == 0   (if W non-empty),
    # and if W is empty, Bad must be empty.
    for c in range(n):
        Nc = adj_pos[c]
        if Nc == 0:
            continue
        for b in range(c):
            if not (Nc >> b) & 1:
                continue  # bc not in E
            Nb = adj_pos[b]
            # Bad: a < b, ab not in E, ac in E
            Bad = (~Nb) & Nc & ((1 << b) - 1)
            if Bad == 0:
                continue
            W = Nb & ~Nc & ((1 << b) - 1)
            if W == 0:
                return False
            minW = (W & -W).bit_length() - 1
            # any bad a <= minW is unwitnessed
            if Bad & ((1 << (minW + 1)) - 1):
                return False
    return True


def _lexbfs(graph):
    """Static LexBFS: return a valid ordering of all vertices."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets of vertices with identical label
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket, take its smallest vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        v = min(buckets[bi])
        buckets[bi].discard(v)
        order.append(v)

        # refine: for each bucket, split off vertices adjacent to v;
        # the adjacent part (label extended with v, lexicographically
        # larger) keeps the bucket's position, the non-adjacent part
        # goes after it
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = set()
            for x in b:
                if graph[v][x]:
                    nb.add(x)
            if nb:
                rest = b - nb
                new_buckets.append(nb)
                if rest:
                    new_buckets.append(rest)
            else:
                new_buckets.append(b)
        buckets = new_buckets

    return order


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    if _is_lexbfs(graph, order):
        return {'ordering': order}
    order = _lexbfs(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = state['ordering']
    if _is_lexbfs(graph, order):
        return {'ordering': order}
    order = _lexbfs(graph)
    return {'ordering': order}
