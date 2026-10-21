"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via adjacency lists.
- insert_edge(u,v): if the current ordering is still valid (checked with the
  (LB) 4-point property using bitmask acceleration), keep it. Otherwise
  recompute from scratch.
- delete_edge(u,v): same check-then-recompute scheme.

The 4-point check uses bitmask adjacency for O(1) witness lookups, making
the O(n^3) check fast in practice.
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


def _adj_masks(adj):
    """Convert adjacency sets to bitmask integers."""
    n = len(adj)
    masks = [0] * n
    for v in range(n):
        m = 0
        for u in adj[v]:
            m |= (1 << u)
        masks[v] = m
    return masks


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


def _is_valid_lexbfs(order, masks):
    """Check the (LB) 4-point property using bitmask adjacency.
    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    # Precompute prefix masks: prefix[a] = bitmask of vertices at positions 0..a-1
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << order[i])

    for a in range(n):
        va = order[a]
        earlier = prefix[a]  # bitmask of vertices at positions < a
        ma = masks[va]
        for b in range(a + 1, n):
            vb = order[b]
            if ma & (1 << vb):
                continue  # ab in E, no constraint
            mb = masks[vb]
            for c in range(b + 1, n):
                vc = order[c]
                if not (ma & (1 << vc)):
                    continue  # ac not in E, no constraint
                # ac in E, ab not in E: need d < a with db in E and dc not in E
                # d must be in earlier, adjacent to vb, not adjacent to vc
                if (earlier & mb & ~masks[vc]) == 0:
                    return False
    return True


def _recompute(graph):
    adj = _adj_lists(graph)
    order = _lexbfs(adj)
    masks = _adj_masks(adj)
    return {'ordering': order, 'adj': adj, 'masks': masks}


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['adj'][v].add(u)
    state['masks'][u] |= (1 << v)
    state['masks'][v] |= (1 << u)
    if _is_valid_lexbfs(state['ordering'], state['masks']):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['adj'][v].discard(u)
    state['masks'][u] &= ~(1 << v)
    state['masks'][v] &= ~(1 << u)
    if _is_valid_lexbfs(state['ordering'], state['masks']):
        return state
    return _recompute(graph)
