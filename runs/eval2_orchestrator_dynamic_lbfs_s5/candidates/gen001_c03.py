"""Dynamic LexBFS ordering (candidate gen001_c03).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge(u, v): if the current ordering is still a valid LexBFS of the
  new graph (checked via the (LB) 4-point property), keep it.  Otherwise
  recompute from scratch.
- delete_edge(u, v): an edge deletion can only destroy validity, so always
  recompute from scratch.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
It is necessary and sufficient for an ordering to be a LexBFS ordering.
"""


def _lexbfs(adj):
    """Static O(n+m) LexBFS via partition refinement.  Returns the ordering."""
    n = len(adj)
    if n == 0:
        return []
    # buckets: list of lists of vertices, in order
    buckets = [[v] for v in range(n)]
    # for each vertex, the index of the bucket it currently sits in
    bucket_of = list(range(n))
    # for each vertex, the index of the vertex inside its bucket
    idx_in = [0] * n

    for s in range(n):
        # refine: split every bucket by adjacency to s
        new_buckets = []
        for b in buckets:
            nb = [v for v in b if adj[v][s] == 1]
            rest = [v for v in b if adj[v][s] == 0]
            if nb:
                new_buckets.append(nb)
            if rest:
                new_buckets.append(rest)
        # rebuild bookkeeping
        buckets = new_buckets
        for bi, b in enumerate(buckets):
            for i, v in enumerate(b):
                bucket_of[v] = bi
                idx_in[v] = i
        # pick next vertex: first bucket, first vertex
        s = buckets[0][0]
        # remove s from its bucket
        b = buckets[bucket_of[s]]
        i = idx_in[s]
        if i + 1 < len(b):
            # move the last vertex into position i
            last = b[-1]
            b[i] = last
            b.pop()
            idx_in[last] = i
        else:
            b.pop()
            if not b:
                buckets.pop(bucket_of[s])
                # recompute bucket_of/idx_in for remaining vertices
                for bi, bb in enumerate(buckets):
                    for j, v in enumerate(bb):
                        bucket_of[v] = bi
                        idx_in[v] = j
    # flatten
    order = []
    for b in buckets:
        order.extend(b)
    return order


def _is_lexbfs(adj, order):
    """Check the (LB) 4-point property.  O(n^3) worst case, early exit."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb] == 1:
                continue
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E
            for c in range(b + 1, n):
                vc = order[c]
                if adj[va][vc] == 1:
                    ok = False
                    for d in range(a):
                        vd = order[d]
                        if adj[vd][vb] == 1 and adj[vd][vc] == 0:
                            ok = True
                            break
                    if not ok:
                        return False
    return True


def init(graph):
    order = _lexbfs(graph)
    return {'ordering': order, 'adj': [row[:] for row in graph]}


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    # check if current ordering is still valid
    if _is_lexbfs(graph, order):
        return {'ordering': order, 'adj': [row[:] for row in graph]}
    order = _lexbfs(graph)
    return {'ordering': order, 'adj': [row[:] for row in graph]}


def delete_edge(graph, edge, state):
    order = _lexbfs(graph)
    return {'ordering': order, 'adj': [row[:] for row in graph]}
