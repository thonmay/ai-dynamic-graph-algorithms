"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
  O(n+m).
- insert_edge: if the new edge (u,v) is consistent with the current
  ordering (i.e. the ordering is still a valid LexBFS), keep it.
  Otherwise recompute from scratch.
- delete_edge: if the old ordering still satisfies the (LB) 4-point
  property, keep it; otherwise recompute.

The (LB) property (Corneil-Krueger): for all positions a < b < c with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # adj as sets
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if row[j]:
                adj[i].add(j)

    # buckets: list of sets; each vertex in exactly one bucket
    buckets = [set(range(n))]
    remaining = set(range(n))
    order = []

    while remaining:
        # pick first non-empty bucket, take its smallest vertex
        bi = 0
        while not buckets[bi]:
            bi += 1
        v = min(buckets[bi])
        buckets[bi].discard(v)
        remaining.discard(v)
        order.append(v)

        # refine all buckets by adjacency to v
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            b1 = set()  # neighbors of v
            b2 = set()  # non-neighbors of v
            for x in b:
                if x in adj[v]:
                    b1.add(x)
                else:
                    b2.add(x)
            if b1:
                new_buckets.append(b1)
            if b2:
                new_buckets.append(b2)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property for the given ordering.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    if n == 0:
        return True

    # pos[v] = position of v in ordering
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    # adj as sets
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if row[j]:
                adj[i].add(j)

    # For each b (position bi), for each c after b not adjacent to b:
    #   for each a before b adjacent to c:
    #     need d before a with d adj b and d not adj c
    for bi in range(n):
        b = ordering[bi]
        for ci in range(bi + 1, n):
            c = ordering[ci]
            if c in adj[b]:
                continue  # b and c adjacent, condition vacuously true
            # b not adj c, pos[b] < pos[c]
            for ai in range(bi):
                a = ordering[ai]
                if a not in adj[c]:
                    continue
                # a adj c, pos[a] < pos[b]
                # need d with pos[d] < pos[a], d adj b, d not adj c
                found = False
                for di in range(ai):
                    d = ordering[di]
                    if d in adj[b] and d not in adj[c]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
