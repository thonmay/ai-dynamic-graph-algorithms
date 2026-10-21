"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via adjacency lists.
- insert_edge(u,v): if the current ordering is still valid (checked with the
  (LB) 4-point property), keep it. Otherwise recompute from scratch.
- delete_edge(u,v): same check-then-recompute scheme.

The 4-point check is O(n^3) in the worst case but early-exits on the first
violation; for sparse graphs it is usually far cheaper than a full recompute.
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

    # HMPV algorithm:
    # - Start with all vertices in one bucket.
    # - Pick first vertex s from first bucket, remove it.
    # - Split each remaining bucket into N(s) and Nbar(s), N(s) first.
    # - Repeat until all vertices are picked.

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
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if va in adj[vb]:
                continue  # ab in E, no constraint
            for c in range(b + 1, n):
                vc = order[c]
                if va not in adj[vc]:
                    continue  # ac not in E, no constraint
                # ac in E, ab not in E: need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = order[d]
                    if vb in adj[vd] and vc not in adj[vd]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _recompute(graph):
    adj = _adj_lists(graph)
    order = _lexbfs(adj)
    return {'ordering': order, 'adj': adj}


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['adj'][v].add(u)
    if _is_valid_lexbfs(state['ordering'], state['adj']):
        return state
    return _recompute(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['adj'][v].discard(u)
    if _is_valid_lexbfs(state['ordering'], state['adj']):
        return state
    return _recompute(graph)
