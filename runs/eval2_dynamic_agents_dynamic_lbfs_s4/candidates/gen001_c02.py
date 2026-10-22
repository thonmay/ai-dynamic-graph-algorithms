"""Dynamic LexBFS ordering (candidate gen001_c02).

Strategy: maintain a valid LexBFS ordering under single edge flips.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n^2) with adjacency matrix.
- insert_edge: try a local "reorder" fix (move the earlier endpoint just
  before the later one, then verify the 4-point property in O(n^3));
  fall back to full recompute if the local fix fails.
- delete_edge: try a local "reorder" fix (move the later endpoint just
  before the earlier one, then verify); fall back to full recompute.

The 4-point (LB) property: for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(adj):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(adj)
    if n == 0:
        return []
    # buckets: list of lists of vertices, in order
    buckets = [[v] for v in range(n)]
    ordered = []
    for _ in range(n):
        # pick first non-empty bucket
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        b = buckets[bi]
        v = b.pop(0)
        ordered.append(v)
        # refine all buckets by adjacency to v
        new_buckets = []
        for other in buckets:
            if not other:
                continue
            nb = [x for x in other if adj[v][x]]
            nnb = [x for x in other if not adj[v][x]]
            if nb:
                new_buckets.append(nb)
            if nnb:
                new_buckets.append(nnb)
        buckets = new_buckets
    return ordered


def _is_valid_lexbfs(adj, order):
    """Check the 4-point (LB) property. O(n^3)."""
    n = len(order)
    for i in range(n):
        a = order[i]
        for j in range(i + 1, n):
            b = order[j]
            if adj[a][b]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > b
            for k in range(j + 1, n):
                c = order[k]
                if not adj[a][c]:
                    continue  # ac not in E
                # need d < a (position < i) with db in E and dc not in E
                found = False
                for t in range(i):
                    d = order[t]
                    if adj[d][b] and not adj[d][c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_reorder(adj, order, u, v, direction):
    """Try moving one endpoint next to the other and verify.

    direction='u_before_v': move u to just before v.
    direction='v_before_u': move v to just before u.
    Returns new order if valid, else None.
    """
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    if direction == 'u_before_v':
        if pos[u] < pos[v]:
            # move u to just before v
            new_order = order[:pos[u]] + order[pos[u] + 1:pos[v]] + [u] + order[pos[v]:]
        else:
            # u is after v; move u to just before v
            new_order = order[:pos[v]] + [u] + order[pos[v]:pos[u]] + order[pos[u] + 1:]
    else:  # v_before_u
        if pos[v] < pos[u]:
            new_order = order[:pos[v]] + order[pos[v] + 1:pos[u]] + [v] + order[pos[u]:]
        else:
            new_order = order[:pos[u]] + [v] + order[pos[u]:pos[v]] + order[pos[v] + 1:]

    if _is_valid_lexbfs(adj, new_order):
        return new_order
    return None


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    order = list(state['ordering'])
    # Try local fix: move u just before v.
    new_order = _try_reorder(graph, order, u, v, 'u_before_v')
    if new_order is None:
        new_order = _try_reorder(graph, order, u, v, 'v_before_u')
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    u, v = edge
    order = list(state['ordering'])
    # Try local fix: move v just before u.
    new_order = _try_reorder(graph, order, u, v, 'v_before_u')
    if new_order is None:
        new_order = _try_reorder(graph, order, u, v, 'u_before_v')
    if new_order is None:
        new_order = _lexbfs(graph)
    return {'ordering': new_order}
