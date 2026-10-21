"""Dynamic LexBFS ordering.

Strategy:
- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via adjacency lists.
- insert_edge / delete_edge: update the adjacency sets, then try a cheap
  local repair of the existing ordering.  If the repair fails the (LB)
  4-point certificate, fall back to a full recompute.

Local repair idea: an edge update (u,v) changes the labels of exactly u and
v, and the labels of every other vertex only in the bit that records
adjacency to u or v.  In practice the old ordering is often still valid, or
becomes valid after moving u and v to their correct positions.  We test a
small family of candidate orderings (keep, swap, move u, move v, move both)
with the O(n^3) (LB) certificate and keep the first that passes.

The (LB) certificate (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _adj_lists(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def _lexbfs(adj):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(adj)
    if n == 0:
        return []

    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        s = buckets[0][0]
        order.append(s)
        buckets[0] = buckets[0][1:]
        if not buckets[0]:
            buckets = buckets[1:]

        new_buckets = []
        for b in buckets:
            n_part = [v for v in b if v in adj[s]]
            nb_part = [v for v in b if v not in adj[s]]
            if n_part:
                new_buckets.append(n_part)
            if nb_part:
                new_buckets.append(nb_part)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(order, adj):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    for ia in range(n):
        a = order[ia]
        adj_a = adj[a]
        for ib in range(ia + 1, n):
            b = order[ib]
            if b in adj_a:
                continue  # ab in E, no constraint
            for ic in range(ib + 1, n):
                c = order[ic]
                if c not in adj_a:
                    continue  # ac not in E, no constraint
                # ac in E, ab not in E: need d < a with db in E and dc not in E
                found = False
                for id_ in range(ia):
                    d = order[id_]
                    if b in adj[d] and c not in adj[d]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _recompute(graph):
    adj = _adj_lists(graph)
    order = _lexbfs(adj)
    return {'ordering': order, 'adj': adj}


def _try_repair(order, adj, u, v):
    """Try a small family of local modifications of `order`.

    Returns a new ordering list if one passes the (LB) certificate,
    otherwise None.
    """
    n = len(order)
    if n == 0:
        return None

    pos = {x: i for i, x in enumerate(order)}
    pu, pv = pos[u], pos[v]

    # Candidate 0: the old ordering is still valid.
    if _is_valid_lexbfs(order, adj):
        return list(order)

    # Candidate 1: swap u and v.
    if pu != pv:
        cand = list(order)
        cand[pu], cand[pv] = cand[pv], cand[pu]
        if _is_valid_lexbfs(cand, adj):
            return cand

    def try_move(cand, x, target):
        i = cand.index(x)
        cand.pop(i)
        if target > i:
            target -= 1
        target = max(0, min(len(cand), target))
        cand.insert(target, x)
        return cand

    # Candidates 2/3: move u (or v) to a different position.
    targets_u = [pv, pv + 1, 0, n - 1, (pu + pv) // 2]
    for t in targets_u:
        cand = try_move(list(order), u, t)
        if _is_valid_lexbfs(cand, adj):
            return cand

    targets_v = [pu, pu + 1, 0, n - 1, (pu + pv) // 2]
    for t in targets_v:
        cand = try_move(list(order), v, t)
        if _is_valid_lexbfs(cand, adj):
            return cand

    # Candidate 4: move both u and v (u first, then v).
    for tu in targets_u:
        cand1 = try_move(list(order), u, tu)
        iv = cand1.index(v)
        for tv in [iv, iv + 1, 0, n - 1]:
            cand2 = try_move(cand1, v, tv)
            if _is_valid_lexbfs(cand2, adj):
                return cand2

    # Candidate 5: move u to every position (O(n) checks).
    for t in range(n):
        if t == pu:
            continue
        cand = try_move(list(order), u, t)
        if _is_valid_lexbfs(cand, adj):
            return cand

    # Candidate 6: move v to every position (O(n) checks).
    for t in range(n):
        if t == pv:
            continue
        cand = try_move(list(order), v, t)
        if _is_valid_lexbfs(cand, adj):
            return cand

    return None


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['adj'][v].add(u)
    repaired = _try_repair(state['ordering'], state['adj'], u, v)
    if repaired is not None:
        state['ordering'] = repaired
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['adj'][v].discard(u)
    repaired = _try_repair(state['ordering'], state['adj'], u, v)
    if repaired is not None:
        state['ordering'] = repaired
        return state
    return _recompute(graph)
