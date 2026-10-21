"""Dynamic LexBFS ordering (candidate gen002_c01).

Derived from gen001_c01.  Changes:
  1. The state carries the adjacency sets (and n) so updates do not rebuild
     the adjacency structure from the matrix; only the flipped edge is
     patched in O(1).
  2. The 4-point (LB) validity check is vectorized with bitsets (Python
     ints as bit masks), which makes the cheap "is the old ordering still
     valid?" test much faster than the parent's O(n^4)-ish nested loops.
  3. The fallback recompute is the same static partition-refinement LexBFS
     (any start vertex, any tie-break), verified with the bitset check.

Correctness:
  - init: static LexBFS, valid by construction.
  - update: if the old ordering still satisfies the (LB) 4-point property
    on the new graph, it is a valid LexBFS and is kept (no recompute).
    Otherwise a full static recompute is performed and verified.
"""


def _selftest():
    import random
    random.seed(12345)
    for trial in range(300):
        n = random.randint(1, 12)
        g = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                if random.random() < 0.4:
                    g[u][v] = g[v][u] = 1
        st = init(g)
        adj = _adj_sets(g)
        masks = _masks(adj, n)
        assert _is_valid_lexbfs(st['ordering'], masks, n), (n, g, st['ordering'])
        # also test a few random edge flips
        for _ in range(5):
            u = random.randrange(n)
            v = random.randrange(n)
            if u == v:
                continue
            if g[u][v] == 0:
                g[u][v] = g[v][u] = 1
                st = insert_edge(g, (u, v), st)
            else:
                g[u][v] = g[v][u] = 0
                st = delete_edge(g, (u, v), st)
            adj = _adj_sets(g)
            masks = _masks(adj, n)
            assert _is_valid_lexbfs(st['ordering'], masks, n), (n, g, st['ordering'])
    print("SELFTEST OK")


def _adj_sets(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    return adj


def _masks(adj, n):
    masks = [0] * n
    for u in range(n):
        m = 0
        for v in adj[u]:
            m |= 1 << v
        masks[u] = m
    return masks


def _lexbfs(adj, n, prefer_order=None):
    """Static partition-refinement LexBFS.

    adj: list of sets (undirected).
    prefer_order: optional list of vertices used as tie-break preference.
    Returns a list of n vertices: a valid LexBFS ordering.
    """
    if prefer_order is not None:
        rank = {v: i for i, v in enumerate(prefer_order)}
    else:
        rank = None

    classes = [[v for v in range(n)]]
    if rank is not None:
        classes[0].sort(key=lambda v: rank[v])

    order = []
    while classes:
        front = classes[0]
        if not front:
            classes.pop(0)
            continue
        v = front[0]
        front.pop(0)
        order.append(v)
        new_classes = []
        for cls in classes:
            if not cls:
                continue
            in_v = [x for x in cls if x in adj[v]]
            not_v = [x for x in cls if x not in adj[v]]
            if in_v:
                if rank is not None:
                    in_v.sort(key=lambda x: rank[x])
                new_classes.append(in_v)
            if not_v:
                if rank is not None:
                    not_v.sort(key=lambda x: rank[x])
                new_classes.append(not_v)
        classes = new_classes
    return order


def _is_valid_lexbfs(order, masks, n):
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Bitset formulation:
      N(v) = adjacency mask of v.
      For a fixed (a, b) with ab not in E:
        D = { d < a : b in N(d) }
        If D is empty: any c > b with c in N(a) is a violation.
        Otherwise: for each c > b with c in N(a), we need some d in D
        with c not in N(d), i.e. c not in (union of N(d) for d in D).
    """
    for a in range(n):
        va = order[a]
        Na = masks[va]
        for b in range(a + 1, n):
            vb = order[b]
            if Na >> vb & 1:
                continue  # ab in E: nothing to check
            # ab not in E
            union = 0
            empty = True
            for d in range(a):
                vd = order[d]
                if masks[vd] >> vb & 1:
                    empty = False
                    union |= masks[vd]
            if empty:
                # any c > b adjacent to a violates
                for c in range(b + 1, n):
                    vc = order[c]
                    if Na >> vc & 1:
                        return False
                continue
            for c in range(b + 1, n):
                vc = order[c]
                if not (Na >> vc & 1):
                    continue
                if not (union >> vc & 1):
                    continue  # some d in D misses c: OK
                return False
    return True


def _recompute(adj, n, prefer_order=None):
    return _lexbfs(adj, n, prefer_order)


def init(graph):
    n = len(graph)
    adj = _adj_sets(graph)
    order = _lexbfs(adj, n)
    return {
        'ordering': order,
        'adj': adj,
        'masks': _masks(adj, n),
        'n': n,
    }


def _patch(state, u, v, present):
    """Flip edge (u, v) in the state's adjacency sets and masks."""
    adj = state['adj']
    masks = state['masks']
    if present:
        adj[u].add(v)
        adj[v].add(u)
        masks[u] |= 1 << v
        masks[v] |= 1 << u
    else:
        adj[u].discard(v)
        adj[v].discard(u)
        masks[u] &= ~(1 << v)
        masks[v] &= ~(1 << u)


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    order = list(state['ordering'])
    _patch(state, u, v, True)

    if _is_valid_lexbfs(order, state['masks'], n):
        return state

    new_order = _recompute(state['adj'], n, prefer_order=order)
    if _is_valid_lexbfs(new_order, state['masks'], n):
        state['ordering'] = new_order
        return state

    new_order = _recompute(state['adj'], n)
    state['ordering'] = new_order
    return state


def delete_edge(graph, edge, state):
    # delete
    u, v = edge
    n = state['n']
    order = list(state['ordering'])
    _patch(state, u, v, False)

    if _is_valid_lexbfs(order, state['masks'], n):
        return state

    new_order = _recompute(state['adj'], n, prefer_order=order)
    if _is_valid_lexbfs(new_order, state['masks'], n):
        state['ordering'] = new_order
        return state

    new_order = _recompute(state['adj'], n)
    state['ordering'] = new_order
    return state
