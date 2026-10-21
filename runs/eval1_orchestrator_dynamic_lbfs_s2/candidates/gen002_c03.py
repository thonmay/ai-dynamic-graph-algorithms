"""Dynamic LexBFS ordering (open tier).

Strategy:
- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot), O(n+m).
- insert_edge(u,v): check if current ordering is still valid via the
  prefix-neighbor characterization in O(n^2); if valid, keep it; else recompute.
- delete_edge(u,v): recompute from scratch (deletion can break validity).

Validity is certified by the prefix-neighbor property: for every prefix P
of the ordering, N(P) ∩ R (where R is the remaining suffix) must be a
prefix of R.  This is equivalent to the (LB) 4-point property of
Corneil-Krueger.
"""


def _lexbfs(adj, n):
    """Static partition-refinement LexBFS (HMPV). Returns an ordering list.

    Algorithm:
    - Maintain a list of buckets (each a list of vertices, in order).
    - Repeatedly: take the first non-empty bucket, take its first vertex x.
      Output x. Split the REMAINDER of that bucket by adjacency to x:
      neighbors of x come first, non-neighbors of x come second.
      Both new sub-buckets are inserted at the front of the bucket list.
    """
    buckets = [list(range(n))]

    order = []
    while True:
        # Find first non-empty bucket
        bi = -1
        for i in range(len(buckets)):
            if buckets[i]:
                bi = i
                break
        if bi == -1:
            break

        b = buckets[bi]
        x = b[0]
        order.append(x)

        # Remove x from its bucket
        b = b[1:]

        # Split the remainder of this bucket by adjacency to x
        adjb = []
        nonadj = []
        for y in b:
            if adj[x][y]:
                adjb.append(y)
            else:
                nonadj.append(y)

        # Replace bucket bi with: adjb (if non-empty), nonadj (if non-empty)
        new_parts = []
        if adjb:
            new_parts.append(adjb)
        if nonadj:
            new_parts.append(nonadj)
        buckets[bi:bi+1] = new_parts

    return order


def _is_valid_lexbfs(adj, n, ordering):
    """Check whether `ordering` is a valid LexBFS ordering of `adj`.

    Uses the prefix-neighbor characterization: for every prefix P of the
    ordering, N(P) ∩ R (where R is the remaining suffix) must be a prefix
    of R.  This is equivalent to the (LB) 4-point property of
    Corneil-Krueger.
    """
    # Precompute neighbor sets
    nbrs = [set() for _ in range(n)]
    for u in range(n):
        row = adj[u]
        for v in range(u + 1, n):
            if row[v]:
                nbrs[u].add(v)
                nbrs[v].add(u)

    # pos[v] = position of vertex v in the ordering
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    # N = set of neighbors of the current prefix P in the remaining R.
    # At step i, P = ordering[:i], R = ordering[i:].
    # We need N to be a prefix of R.
    N = set()
    for i in range(n):
        # Check: N must be a prefix of R = ordering[i:].
        # That is, there exists k >= i such that
        #   N = { ordering[i], ordering[i+1], ..., ordering[k-1] }
        # (or N is empty, which corresponds to k = i).
        # Equivalently: scanning R from position i, all vertices in N
        # come before all vertices not in N.
        seen_non_n = False
        for j in range(i, n):
            v = ordering[j]
            if v in N:
                if seen_non_n:
                    return False  # a vertex in N appears after a non-N vertex
            else:
                seen_non_n = True
        # Update N: add ordering[i] to P, so add its neighbors in R to N.
        x = ordering[i]
        for y in nbrs[x]:
            if pos[y] > i:  # y is in R
                N.add(y)
        N.discard(x)

    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    ordering = state['ordering']
    # Check if the current ordering is still valid
    if _is_valid_lexbfs(graph, n, ordering):
        return state
    # Otherwise recompute
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    # Deletion can break validity; recompute
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}
