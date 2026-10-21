"""Dynamic LexBFS ordering (candidate gen003_c01).

Derived from gen002_c01.  Changes:
  1. The state carries only the adjacency masks (and n); the adjacency
     sets are dropped.  Updates patch the two masks in O(1).
  2. The static partition-refinement LexBFS is now O(n^2) bitset
     operations (classes are lists of bit masks; refinement is a single
     AND per class per step) instead of the parent's O(n^2)
     set-membership tests with per-class sorting.  This makes the
     fallback recompute much cheaper.
  3. The recompute fallback is simplified: a single static LexBFS run
     (deterministic, valid by construction) replaces the parent's
     "prefer old order, else plain" double recompute.
  4. The (LB) 4-point validity check keeps the parent's bitset
     formulation (O(n^3) bit operations worst case).  An attempted
     O(n^2) incremental variant was found to be incorrect on the
     public examples and was reverted.

Correctness:
  - init: static LexBFS, valid by construction.
  - update: if the old ordering still satisfies the (LB) 4-point property
    on the new graph, it is a valid LexBFS and is kept (no recompute).
    Otherwise a full static recompute is performed.
"""


def _adj_masks(graph):
    n = len(graph)
    masks = [0] * n
    for u in range(n):
        row = graph[u]
        m = 0
        for v in range(u + 1, n):
            if row[v]:
                m |= 1 << v
        masks[u] = m
    return masks


def _lexbfs(masks, n):
    """Static partition-refinement LexBFS using bitsets.

    masks: list of int adjacency masks (undirected).
    Returns a list of n vertices: a valid LexBFS ordering.

    Each class is a list of bit masks (one per vertex in the class).  The
    classes are kept in a list; the first class is the current front.
    Refinement by a chosen vertex v splits each class into (C & N(v)) and
    (C & ~N(v)), preserving the order of vertices inside each part.
    """
    classes = [[1 << v for v in range(n)]]
    order = []
    while classes:
        front = classes[0]
        if not front:
            classes.pop(0)
            continue
        vmask = front.pop(0)
        v = vmask.bit_length() - 1
        order.append(v)
        Nv = masks[v]
        new_classes = []
        for cls in classes:
            if not cls:
                continue
            in_v = [m for m in cls if m & Nv]
            not_v = [m for m in cls if not (m & Nv)]
            if in_v:
                new_classes.append(in_v)
            if not_v:
                new_classes.append(not_v)
        classes = new_classes
    return order


def _is_valid_lexbfs_ref(order, masks, n):
    """Reference (LB) 4-point check, O(n^4) bit tests.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
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


def init(graph):
    n = len(graph)
    masks = _adj_masks(graph)
    order = _lexbfs(masks, n)
    return {
        'ordering': order,
        'masks': masks,
        'n': n,
    }


def _patch(state, u, v, present):
    """Flip edge (u, v) in the state's adjacency masks."""
    masks = state['masks']
    if present:
        masks[u] |= 1 << v
        masks[v] |= 1 << u
    else:
        masks[u] &= ~(1 << v)
        masks[v] &= ~(1 << u)


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    order = state['ordering']
    _patch(state, u, v, True)

    if _is_valid_lexbfs_ref(order, state['masks'], n):
        return state

    state['ordering'] = _lexbfs(state['masks'], n)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    order = state['ordering']
    _patch(state, u, v, False)

    if _is_valid_lexbfs_ref(order, state['masks'], n):
        return state

    state['ordering'] = _lexbfs(state['masks'], n)
    return state
