"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering across edge updates. After an
update, first check whether the previous ordering is still a valid LexBFS
ordering of the new graph using the (LB) 4-point property of Corneil and
Krueger:

    for all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

Because a single edge flip only changes the truth value of the property
for triples involving that edge, the check is local:

  * insertion of (u, v): the only triples that can newly fail are those
    where (u, v) plays the role of the edge ac (the edge that must be in
    E). For each such triple (a, b, c) with a and c being u and v, we
    check the witness condition.
  * deletion of (u, v): the only triples that can newly fail are those
    where (u, v) played the role of the witness edge db. For each such
    triple (a, b, c) with d=u, b=v (or d=v, b=u), we check whether
    another witness exists.

If the local check passes, the ordering is still valid and we return it
unchanged (no recomputation). If it fails, we recompute a static LexBFS
ordering via partition refinement, using the previous ordering as a hint
for the start vertex and for tie-breaking.

State: dict with 'ordering' (list of all n vertices, a valid LexBFS
ordering) and 'n'.
"""


def _refine(buckets, v, graph):
    """Split every bucket by adjacency to v. Each bucket is replaced
    in place by its neighbor part (first) and its non-neighbor part
    (second), at the same queue position."""
    out = []
    for b in buckets:
        if not b:
            continue
        nb = [x for x in b if graph[x][v]]
        non = [x for x in b if not graph[x][v]]
        if nb:
            out.append(nb)
        if non:
            out.append(non)
    return out


def _lexbfs(graph, n, start, rank):
    """Static LexBFS via partition refinement.

    Buckets are kept as lists (not sets) so that refinement is
    deterministic and tie-breaking by (rank, id) is well-defined.
    """
    if n == 0:
        return []

    # buckets: list of lists of unprocessed vertices, in queue order
    buckets = [[v for v in range(n) if v != start]]

    order = [start]

    # the start vertex's adjacency must split the initial bucket
    buckets = _refine(buckets, start, graph)

    for _ in range(n - 1):
        # pick next vertex: first non-empty bucket, min by (rank, id)
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi >= len(buckets):
            break
        v = min(buckets[bi], key=lambda x: (rank[x], x))
        buckets[bi].remove(v)
        order.append(v)

        # refine all buckets by adjacency to v, each bucket replaced
        # in place by (neighbor part, non-neighbor part)
        buckets = _refine(buckets, v, graph)

    return order


def _is_valid_lexbfs(order, graph, n):
    """Check the (LB) 4-point property of Corneil and Krueger.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Returns True iff the ordering is a valid LexBFS ordering.
    """
    if n == 0:
        return True
    if len(order) != n:
        return False
    if sorted(order) != list(range(n)):
        return False

    # Direct O(n^3) check with early exit: iterate over triples
    # (a, b, c) with a < b < c in position.
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if graph[a][b]:
                continue  # ab in E, condition not triggered
            # ab not in E; now check all c > b
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue  # ac not in E, condition not triggered
                # ac in E and ab not in E: need d < a with db in E and dc not in E
                found = False
                for d_idx in range(i):
                    d = order[d_idx]
                    if graph[d][b] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _local_insert_ok(order, pos, u, v, graph, n):
    """After inserting edge (u, v), check only the triples that can
    newly fail: those where (u, v) plays the role of the edge ac (the
    edge that must be in E).

    Case 1: a=u, c=v (pos(u) < pos(v)).
      b is any vertex with pos(u) < pos(b) < pos(v).
      Condition triggers if ub not in E.
      Need witness d with pos(d) < pos(u), d·b in E, d·v not in E.

    Case 2: a=v, c=u (pos(v) < pos(u)).
      b is any vertex with pos(v) < pos(b) < pos(u).
      Condition triggers if vb not in E.
      Need witness d with pos(d) < pos(v), d·b in E, d·u not in E.

    Returns True iff the ordering is still valid.
    """
    i = pos[u]
    j = pos[v]
    if i < j:
        # Case 1: a=u, c=v
        for b_idx in range(i + 1, j):
            b = order[b_idx]
            if graph[u][b]:
                continue  # ub in E, condition not triggered
            # ub not in E; need witness d < u with d·b in E and d·v not in E
            found = False
            for d_idx in range(i):
                d = order[d_idx]
                if graph[d][b] and not graph[d][v]:
                    found = True
                    break
            if not found:
                return False
    else:
        # Case 2: a=v, c=u
        for b_idx in range(j + 1, i):
            b = order[b_idx]
            if graph[v][b]:
                continue  # vb in E, condition not triggered
            # vb not in E; need witness d < v with d·b in E and d·u not in E
            found = False
            for d_idx in range(j):
                d = order[d_idx]
                if graph[d][b] and not graph[d][u]:
                    found = True
                    break
            if not found:
                return False
    return True


def _local_delete_ok(order, pos, u, v, graph, n):
    """After deleting edge (u, v), check only the triples that can
    newly fail: those where (u, v) played the role of the witness edge
    db.

    Case 1: d=u, b=v (pos(u) < pos(v)).
      a is any vertex with pos(u) < pos(a) < pos(v).
      c is any vertex with pos(c) > pos(v).
      Condition: ac in E and av not in E.
      Previously witness was d=u (uv in E, uc not in E).
      After deletion, need another d' < a with d'v in E and d'c not in E.

    Case 2: d=v, b=u (pos(v) < pos(u)).
      a is any vertex with pos(v) < pos(a) < pos(u).
      c is any vertex with pos(c) > pos(u).
      Condition: ac in E and av not in E.
      Previously witness was d=v (vu in E, vc not in E).
      After deletion, need another d' < a with d'u in E and d'c not in E.

    Returns True iff the ordering is still valid.
    """
    i = pos[u]
    j = pos[v]
    if i < j:
        # Case 1: d=u, b=v
        for a_idx in range(i + 1, j):
            a = order[a_idx]
            if graph[a][v]:
                continue  # av in E, condition not triggered
            # av not in E; check all c after v
            for k in range(j + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue  # ac not in E, condition not triggered
                # ac in E and av not in E: need d' < a with d'v in E and d'c not in E
                found = False
                for d_idx in range(a_idx):
                    d = order[d_idx]
                    if graph[d][v] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    else:
        # Case 2: d=v, b=u
        for a_idx in range(j + 1, i):
            a = order[a_idx]
            if graph[a][u]:
                continue  # au in E, condition not triggered
            # au not in E; check all c after u
            for k in range(i + 1, n):
                c = order[k]
                if not graph[a][c]:
                    continue  # ac not in E, condition not triggered
                # ac in E and au not in E: need d' < a with d'u in E and d'c not in E
                found = False
                for d_idx in range(a_idx):
                    d = order[d_idx]
                    if graph[d][u] and not graph[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _recompute(graph, state):
    n = state['n']
    hint = state['ordering']
    if not hint:
        start = 0
        rank = [i for i in range(n)]
    else:
        start = hint[0]
        rank = [0] * n
        for i, v in enumerate(hint):
            rank[v] = i
    order = _lexbfs(graph, n, start, rank)
    return {'ordering': order, 'n': n}


def init(graph):
    n = len(graph)
    order = _lexbfs(graph, n, 0, [i for i in range(n)])
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    u, v = edge
    pos = {v: i for i, v in enumerate(order)}
    if _local_insert_ok(order, pos, u, v, graph, n):
        return state
    return _recompute(graph, state)


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    u, v = edge
    pos = {v: i for i, v in enumerate(order)}
    if _local_delete_ok(order, pos, u, v, graph, n):
        return state
    return _recompute(graph, state)
