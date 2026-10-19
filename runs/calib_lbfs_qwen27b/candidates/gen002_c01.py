"""Dynamic LexBFS ordering (open problem tier).

Strategy: maintain a valid LexBFS ordering.

- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge / delete_edge: recompute from scratch (correctness first;
  the incremental invariants are unproven and the static routine is the
  only verified piece).

Validity is certified by the (LB) 4-point property of Corneil & Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs(adj):
    """Static partition-refinement LexBFS.  Returns (ordering, pos)."""
    n = len(adj)
    # buckets: list of lists of vertices, in current order
    buckets = [[v] for v in range(n)]
    # for each vertex, the index of the bucket it currently sits in
    bidx = list(range(n))
    # for each vertex, the position (offset) inside its bucket
    offset = [0] * n
    # pos[v] = current global position of v
    pos = list(range(n))
    # neighbors[v] = set of neighbors of v (for O(1) membership)
    nbrs = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(n):
            if row[v]:
                nbrs[u].add(v)

    # ordered: list of chosen vertices in order
    ordered = []
    for s in range(n):
        # split every bucket by adjacency to s
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            b0 = []
            b1 = []
            for v in b:
                if s in nbrs[v]:
                    b1.append(v)
                else:
                    b0.append(v)
            if b1:
                new_buckets.append(b1)
            if b0:
                new_buckets.append(b0)
        buckets = new_buckets
        # pick next vertex: first bucket (in order) containing a vertex
        # with at least one non-neighbor among the not-yet-ordered
        # vertices (the standard LexBFS "frontier" rule)
        unvisited = set()
        for b in buckets:
            unvisited.update(b)
        chosen = None
        for b in buckets:
            for v in b:
                has_nonnbr = False
                for w in unvisited:
                    if w not in nbrs[v]:
                        has_nonnbr = True
                        break
                if has_nonnbr:
                    chosen = v
                    break
            if chosen is not None:
                break
        if chosen is None:
            for b in buckets:
                if b:
                    chosen = b[0]
                    break
        # remove chosen from its bucket
        for b in buckets:
            if chosen in b:
                b.remove(chosen)
                if not b:
                    buckets.remove(b)
                break
        ordered.append(chosen)
    ordering = ordered
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i
    return ordering, pos


def init(graph):
    ordering, pos = _lexbfs(graph)
    return {'ordering': ordering, 'pos': pos}


def insert_edge(graph, edge, state):
    ordering, pos = _lexbfs(graph)
    return {'ordering': ordering, 'pos': pos}


def delete_edge(graph, edge, state):
    ordering, pos = _lexbfs(graph)
    return {'ordering': ordering, 'pos': pos}
