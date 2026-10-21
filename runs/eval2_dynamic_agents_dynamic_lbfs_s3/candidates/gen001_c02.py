"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, recompute
a full O(n^2) partition-refinement LexBFS using the previous ordering
as tie-break (to minimize disruption). The (LB) 4-point property
(Corneil-Krueger) certifies validity.
"""


def _lexbfs(graph, n, order_hint=None):
    """Full LexBFS via partition refinement.

    order_hint: optional list of vertices used as tie-break (vertices
    appearing earlier in the hint are preferred). If None, tie-break by
    vertex id.
    """
    if n == 0:
        return []
    if order_hint is None:
        rank = list(range(n))
    else:
        pos = [0] * n
        for i, v in enumerate(order_hint):
            pos[v] = i
        rank = pos

    # buckets: list of lists of vertices, in current order
    buckets = [[v] for v in range(n)]
    # adjacency bitsets for fast refinement
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= (1 << v)
        adj[u] = bits

    order = []
    remaining = n
    while remaining > 0:
        # pick the first non-empty bucket
        bi = 0
        while not buckets[bi]:
            bi += 1
        v = buckets[bi].pop(0)
        order.append(v)
        remaining -= 1
        if not buckets[bi]:
            del buckets[bi]
            continue
        # refine bucket bi by adjacency to v
        b = buckets[bi]
        if len(b) <= 1:
            continue
        # split into neighbors and non-neighbors of v, preserving order
        # within each part, tie-broken by rank
        neigh = []
        non = []
        for w in b:
            if (adj[v] >> w) & 1:
                neigh.append(w)
            else:
                non.append(w)
        # sort each part by rank (stable refinement)
        neigh.sort(key=lambda w: rank[w])
        non.sort(key=lambda w: rank[w])
        if neigh and non:
            buckets[bi] = neigh
            buckets.insert(bi + 1, non)
        else:
            buckets[bi] = neigh + non
    return order


def _is_lexbfs(graph, n, order):
    """Check the (LB) 4-point property."""
    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= (1 << v)
        adj[u] = bits
    for b in range(n):
        bv = order[b]
        nb = adj[bv]
        for a in range(b):
            av = order[a]
            if (nb >> av) & 1:
                continue  # ab in E, skip
            # ab not in E; check all c > b with ac in E
            # need: exists d < a with db in E and dc not in E
            D = 0
            for d in range(a):
                dv = order[d]
                if (nb >> dv) & 1:
                    D |= (1 << dv)
            if D == 0:
                na = adj[av]
                for c in range(b + 1, n):
                    cv = order[c]
                    if (na >> cv) & 1:
                        return False
                continue
            na = adj[av]
            for c in range(b + 1, n):
                cv = order[c]
                if (na >> cv) & 1:
                    nc = adj[cv]
                    if D & ~nc == 0:
                        return False
    return True


def _try_repair(graph, n, order, u, v):
    """Try to repair the ordering after adding/removing edge (u, v).
    
    Strategy: try moving u and v to various positions and check if the
    result is a valid LexBFS. If so, return the repaired ordering.
    Otherwise return None.
    """
    # First, try the current ordering (maybe it's still valid)
    if _is_lexbfs(graph, n, order):
        return list(order)
    
    # Try moving u to each position
    for i in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(i, u)
        if _is_lexbfs(graph, n, new_order):
            return new_order
    
    # Try moving v to each position
    for i in range(n):
        new_order = list(order)
        new_order.remove(v)
        new_order.insert(i, v)
        if _is_lexbfs(graph, n, new_order):
            return new_order
    
    # Try moving u to position i, then v to position j
    for i in range(n):
        new_order = list(order)
        new_order.remove(u)
        new_order.insert(i, u)
        for j in range(n):
            new_order2 = list(new_order)
            new_order2.remove(v)
            new_order2.insert(j, v)
            if _is_lexbfs(graph, n, new_order2):
                return new_order2
    
    return None


def init(graph):
    n = len(graph)
    order = _lexbfs(graph, n)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    # Try cheap repair first
    repaired = _try_repair(graph, n, state['ordering'], u, v)
    if repaired is not None:
        state['ordering'] = repaired
        return state
    # Full recompute
    order = _lexbfs(graph, n, order_hint=state['ordering'])
    state['ordering'] = order
    return state


def delete_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    repaired = _try_repair(graph, n, state['ordering'], u, v)
    if repaired is not None:
        state['ordering'] = repaired
        return state
    order = _lexbfs(graph, n, order_hint=state['ordering'])
    state['ordering'] = order
    return state
