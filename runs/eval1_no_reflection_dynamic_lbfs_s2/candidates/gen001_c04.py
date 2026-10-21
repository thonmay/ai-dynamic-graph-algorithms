"""Dynamic LexBFS ordering (candidate gen001_c04).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot)
  with a deterministic tie-break (smallest vertex id first).
- insert_edge(u,v): if the current ordering is already valid for the new graph,
  keep it. Otherwise recompute.
- delete_edge(u,v): revalidate; recompute if invalid.

Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs(n, adj):
    """Static LexBFS via partition refinement. Returns ordering list."""
    # Build neighbor sets
    nbrs = [set() for _ in range(n)]
    for i in range(n):
        row = adj[i]
        for j in range(i + 1, n):
            if row[j]:
                nbrs[i].add(j)
                nbrs[j].add(i)

    # buckets: list of lists of vertices
    buckets = [list(range(n))]
    order = []

    while True:
        # Find first non-empty bucket
        bi = -1
        for i, b in enumerate(buckets):
            if b:
                bi = i
                break
        if bi == -1:
            break

        # Pick first vertex from this bucket
        x = buckets[bi][0]
        buckets[bi] = buckets[bi][1:]

        # Refine all other buckets by N(x)
        new_buckets = []
        for i, b in enumerate(buckets):
            if i == bi:
                new_buckets.append(b)
                continue
            if not b:
                new_buckets.append(b)
                continue
            # Split b into N(x) and non-N(x), with N(x) first
            in_nbr = [v for v in b if v in nbrs[x]]
            not_nbr = [v for v in b if v not in nbrs[x]]
            new_buckets.append(in_nbr)
            new_buckets.append(not_nbr)

        buckets = new_buckets
        order.append(x)

    return order


def _check_validity(n, adj, order):
    """Check if order is a valid LexBFS ordering using the (LB) property.
    Returns True if valid, False otherwise.
    
    (LB): for all a < b < c (positions in order) with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    # Build adjacency bitmasks
    adj_bits = [0] * n
    for i in range(n):
        bits = 0
        for j in range(n):
            if adj[i][j]:
                bits |= (1 << j)
        adj_bits[i] = bits

    # Build prefix bitmasks: prefix_bits[i] = bitmask of vertices at positions < i
    prefix_bits = [0] * (n + 1)
    for i in range(n):
        prefix_bits[i + 1] = prefix_bits[i] | (1 << order[i])

    # Check the (LB) property
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            # Check if ab not in E
            if adj_bits[va] & (1 << vb):
                continue  # ab in E, skip
            # For each c > b with ac in E
            for c in range(b + 1, n):
                vc = order[c]
                if not (adj_bits[va] & (1 << vc)):
                    continue  # ac not in E, skip
                # Need: exists d < a with db in E and dc not in E
                # = (adj_bits[vb] & prefix_bits[a]) & ~adj_bits[vc] != 0
                if (adj_bits[vb] & prefix_bits[a]) & ~adj_bits[vc] == 0:
                    return False
    return True


def _recompute(n, adj):
    """Recompute the LexBFS ordering and validity."""
    order = _lexbfs(n, adj)
    valid = _check_validity(n, adj, order)
    return order, valid


def init(graph):
    n = len(graph)
    order = _lexbfs(n, graph)
    valid = _check_validity(n, graph, order)
    return {
        'ordering': order,
        'n': n,
        'valid': valid,
    }


def insert_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    order = state['ordering']

    # Recheck validity (adding an edge can create new violations)
    valid = _check_validity(n, graph, order)
    if not valid:
        order, valid = _recompute(n, graph)

    return {
        'ordering': order,
        'n': n,
        'valid': valid,
    }


def delete_edge(graph, edge, state):
    n = state['n']
    u, v = edge
    order = state['ordering']

    # Recheck validity (deleting an edge can create new violations)
    valid = _check_validity(n, graph, order)
    if not valid:
        order, valid = _recompute(n, graph)

    return {
        'ordering': order,
        'n': n,
        'valid': valid,
    }
