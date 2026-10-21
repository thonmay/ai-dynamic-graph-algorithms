"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, recompute
a full O(n^2) label-based LexBFS using the previous ordering as
tie-break (to minimize disruption). The (LB) 4-point property
(Corneil-Krueger) certifies validity.
"""


def _lexbfs(graph, n, order_hint=None):
    """Full LexBFS via label refinement (textbook algorithm).

    Repeatedly pick the remaining vertex with the maximum label
    (bitstring of adjacencies to already-output vertices, in output
    order), append it, and extend every remaining label with the
    adjacency bit to the picked vertex. Ties are broken by position
    in order_hint (or vertex id if no hint).
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

    adj = [0] * n
    for u in range(n):
        row = graph[u]
        bits = 0
        for v in range(n):
            if row[v]:
                bits |= (1 << v)
        adj[u] = bits

    remaining = list(range(n))
    labels = {v: 0 for v in range(n)}
    order = []
    for step in range(n):
        # pick max label, tie-break by rank (earlier in hint wins)
        best = None
        for v in remaining:
            key = (labels[v], -rank[v])
            if best is None or key > best[0]:
                best = (key, v)
        v = best[1]
        order.append(v)
        remaining.remove(v)
        bit = 1 << step
        for w in remaining:
            if (adj[v] >> w) & 1:
                labels[w] |= bit
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
