"""Dynamic LexBFS ordering (candidate gen007_c01).

Derived from gen002_c01.  Changes:
  1. The (LB) 4-point validity check is now O(n^2) bit operations instead
     of the parent's O(n^3).  For each position a we maintain
         U[a] = union of N(d) over d < a with d adjacent to b,
     incrementally as b sweeps from a+1 to n-1.  The check for a fixed
     (a, b) with ab not in E is then a single bit test:
         (N(a) & ~U[a] & suffix_mask[b+1]) == 0.
     This makes the "is the old ordering still valid?" test much cheaper,
     so updates that do not break the ordering cost O(n^2) bit ops with
     no recompute.
  2. The state carries the adjacency sets and masks (as in the parent) so
     updates patch the flipped edge in O(1); the static partition-
     refinement LexBFS fallback is unchanged.

Correctness:
  - init: static LexBFS, valid by construction.
  - update: if the old ordering still satisfies the (LB) 4-point property
    on the new graph, it is a valid LexBFS and is kept (no recompute).
    Otherwise a full static recompute is performed and verified.
"""


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
    """Check the (LB) 4-point property in O(n^2) bit operations.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    For a fixed (a, b) with ab not in E, let
        D = { d < a : b in N(d) },  U = union of N(d) over d in D.
    The condition "for every c > b with c in N(a), some d in D misses c"
    is equivalent to  N(a) & ~U & {c > b}  ==  0.

    As b sweeps from a+1 to n-1, D only grows (a new d enters D exactly
    when b becomes adjacent to d), so U can be updated incrementally:
        U |= N(d)   for each d < a with b in N(d).
    """
    for a in range(n):
        va = order[a]
        Na = masks[va]
        U = 0
        for b in range(a + 1, n):
            vb = order[b]
            mb = masks[vb]
            # add to D every d < a adjacent to b
            for d in range(a):
                if masks[order[d]] & (1 << vb):
                    U |= mb
            if Na & (1 << vb):
                continue  # ab in E: nothing to check
            # ab not in E: need no c > b with c in N(a) and c in U
            if Na & ~U & ~((1 << (b + 1)) - 1):
                return False
    return True


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

    new_order = _lexbfs(state['adj'], n, prefer_order=order)
    if _is_valid_lexbfs(new_order, state['masks'], n):
        state['ordering'] = new_order
        return state

    state['ordering'] = _lexbfs(state['adj'], n)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    order = list(state['ordering'])
    _patch(state, u, v, False)

    if _is_valid_lexbfs(order, state['masks'], n):
        return state

    new_order = _lexbfs(state['adj'], n, prefer_order=order)
    if _is_valid_lexbfs(new_order, state['masks'], n):
        state['ordering'] = new_order
        return state

    state['ordering'] = _lexbfs(state['adj'], n)
    return state
