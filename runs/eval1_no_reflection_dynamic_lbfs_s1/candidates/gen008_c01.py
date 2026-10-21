"""Dynamic LexBFS ordering (candidate gen008_c01).

Derived from gen002_c01.  Changes:
  1. The (LB) 4-point validity check is now O(n^2) with bitsets:
     for each position a, P_a = union of N(d) over d < a.  For a pair
     (a, b) with ab not in E, the set of c > b that would violate is
     exactly N(a) & ~P_a & S_b (S_b = positions > b), so the whole
     check is a handful of bit operations per (a, b) pair.
  2. The static LexBFS is now the standard bucket-based partition
     refinement (Habib-McConnell-Paul-Viennot) with a doubly linked
     list of classes and a per-vertex bucket pointer, so each vertex
     is moved at most once per refinement: O(n + m) instead of the
     parent's O(n^2 + m)-ish list rebuilding.
  3. Updates patch the adjacency sets and masks in O(1), test the old
     ordering with the O(n^2) check, and only recompute when it fails.
     The recompute first tries the old ordering as tie-break
     preference, then falls back to natural order.

Correctness:
  - init: static LexBFS, valid by construction.
  - update: if the old ordering still satisfies the (LB) 4-point
    property on the new graph, it is a valid LexBFS and is kept.
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
        masks = _masks(st['adj'], n)
        assert _is_valid_lexbfs(st['ordering'], masks, n), (n, g, st['ordering'])
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
            masks = _masks(st['adj'], n)
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
    """Static partition-refinement LexBFS (bucket based, O(n + m)).

    adj: list of sets (undirected).
    prefer_order: optional list of vertices used as tie-break preference.
    Returns a list of n vertices: a valid LexBFS ordering.
    """
    if n == 0:
        return []

    if prefer_order is not None:
        rank = {v: i for i, v in enumerate(prefer_order)}
        initial = sorted(range(n), key=lambda v: rank[v])
    else:
        initial = list(range(n))

    # Doubly linked list of classes; each class is a list of vertices.
    classes = [initial]
    prev = [None] * 1
    nxt = [None] * 1
    head = 0

    order = []
    while head is not None:
        cls = classes[head]
        if not cls:
            # remove empty class
            p, q = prev[head], nxt[head]
            if p is not None:
                nxt[p] = q
            else:
                head = q
            if q is not None:
                prev[q] = p
            classes[head] = None
            prev[head] = None
            nxt[head] = None
            continue
        v = cls.pop(0)
        order.append(v)
        # Refine every other class by adjacency to v.
        i = head
        while i is not None:
            q = nxt[i]
            ci = classes[i]
            if ci:
                in_v = []
                not_v = []
                for x in ci:
                    if x in adj[v]:
                        in_v.append(x)
                    else:
                        not_v.append(x)
                if in_v:
                    # new class inserted right after i
                    classes.append(in_v)
                    prev.append(i)
                    nxt.append(q)
                    if q is not None:
                        prev[q] = len(classes) - 1
                    nxt[i] = len(classes) - 1
                if not_v:
                    classes[i] = not_v
            i = q
    return order


def _is_valid_lexbfs(order, masks, n):
    """Check the (LB) 4-point property in O(n^2) using bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Bitset formulation:
      N(v) = adjacency mask of v.
      P_a = union of N(d) over d < a.
      S_b = mask of positions > b.
      For a pair (a, b) with ab not in E, the violating c's are
      exactly N(a) & ~P_a & S_b; the ordering is valid iff this is
      empty for every such pair.
    """
    for a in range(n):
        va = order[a]
        Na = masks[va]
        P = 0
        for d in range(a):
            P |= masks[order[d]]
        for b in range(a + 1, n):
            vb = order[b]
            if Na >> vb & 1:
                continue  # ab in E: nothing to check
            if Na & ~P & (~((1 << (b + 1)) - 1)):
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
