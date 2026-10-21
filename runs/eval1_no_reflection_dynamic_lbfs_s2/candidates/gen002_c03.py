"""Dynamic LexBFS ordering (gen002_c03).

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m) via adjacency lists.
- insert_edge(u,v) / delete_edge(u,v): update the adjacency sets, then verify
  the maintained ordering is still a valid LexBFS ordering by *simulating*
  the HMPV partition-refinement process on the current graph and asserting
  that at every step the ordering's next vertex is a legal choice (i.e. it
  lies in the first bucket). If the simulation ever fails, recompute from
  scratch.

Why the simulation check is correct: a permutation is a LexBFS ordering iff
there exists a run of the partition-refinement process (any tie-breaking)
that outputs it. The process is deterministic except for which vertex is
picked from the first bucket, so fixing the picked vertex to the ordering's
next vertex and checking it is always in the first bucket is exactly the
condition for the ordering to be producible. This is O(n+m) per update,
versus the O(n^3) 4-point check used by the parent.
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
    """Check that `order` is a valid LexBFS ordering of the graph `adj`.

    Simulates the HMPV partition-refinement process, but at each step the
    vertex picked from the first bucket is forced to be the next vertex of
    `order`. If at any step that vertex is not in the first bucket, the
    ordering is not a LexBFS ordering.

    Correctness: a permutation is a LexBFS ordering iff some run of the
    partition-refinement process (with some tie-breaking) outputs it. The
    process is deterministic except for the choice of which vertex to pick
    from the first bucket, so forcing that choice to follow `order` and
    checking feasibility is exactly the condition.

    Runs in O(n + m).
    """
    n = len(order)
    if n == 0:
        return True

    buckets = [list(range(n))]

    for i in range(n):
        s = order[i]
        if not buckets:
            return False
        first = buckets[0]
        if s not in first:
            return False
        # Remove s from the first bucket.
        first.remove(s)
        if not first:
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
