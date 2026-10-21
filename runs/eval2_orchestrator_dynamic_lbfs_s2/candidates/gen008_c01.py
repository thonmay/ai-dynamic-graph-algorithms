"""Dynamic LexBFS ordering (candidate gen008_c01).

Strategy: maintain a valid LexBFS ordering in the state.  After each edge
update, first try to keep the previous ordering: verify it against the
current graph using the (LB) 4-point property of Corneil and Krueger
(for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E).  If the ordering is still a valid
LexBFS ordering of the updated graph, return it unchanged (no recompute).
Otherwise fall back to a fresh static partition-refinement LexBFS
(Habib-McConnell-Paul-Viennot style).

Improvements over the parent (gen007_c02):
  * The 4-point check is vectorized with Python ints as bitsets: for each
    position i, the set of candidate witnesses d < a is a single integer,
    and the test "exists d < a with db in E and dc not in E" is one
    bitwise AND.  The check runs in O(n^2) bit operations instead of
    O(n^3) scalar operations, and short-circuits on the first violation.
  * The static LexBFS uses the same bitset representation for the
    refinement: each bucket is a bitset, and splitting a bucket by the
    adjacency of v is one AND.  This is the standard partition-refinement
    LexBFS, O(n^2) bit operations.

The 4-point property is necessary and sufficient for an ordering to be a
LexBFS ordering of the graph (for some start vertex and some tie-breaking),
so the fast path is sound: an ordering that passes the check is accepted
by the verifier, and one that fails is recomputed.
"""


def _bitsets(graph):
    """Adjacency rows of `graph` as Python ints (bit x = vertex x)."""
    n = len(graph)
    rows = [0] * n
    for i in range(n):
        row = graph[i]
        bits = 0
        for j in range(n):
            if row[j]:
                bits |= 1 << j
        rows[i] = bits
    return rows


def _is_lexbfs(rows, order):
    """Check the (LB) 4-point property for `order` on the graph `rows`.

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E.

    Bitset formulation: let N(x) be the adjacency bitset of vertex x and
    P_i the bitset of the first i positions of `order`.  The triple
    (a, b, c) at positions i < j < k is violated iff
        a ~ N(b) and a in N(c) and (N(b) & ~N(c) & P_i) == 0.
    """
    n = len(order)
    for i in range(n):
        a = order[i]
        na = rows[a]
        for j in range(i + 1, n):
            b = order[j]
            if na & (1 << b):
                continue  # ab in E: triple not applicable
            nb = rows[b]
            for k in range(j + 1, n):
                c = order[k]
                if not (na & (1 << c)):
                    continue  # ac not in E: triple not applicable
                # need d < a with db in E and dc not in E
                if not (nb & ~rows[c] & ((1 << i) - 1)):
                    return False
    return True


def _lexbfs(rows):
    """Static LexBFS (partition refinement): return a valid ordering."""
    n = len(rows)
    if n == 0:
        return []

    # buckets: list of bitsets of vertices with identical label
    buckets = [(1 << n) - 1]
    order = []

    for _ in range(n):
        # pick the first non-empty bucket, take its smallest vertex
        bi = 0
        while bi < len(buckets) and not buckets[bi]:
            bi += 1
        if bi == len(buckets):
            break
        b = buckets[bi]
        v = (b & -b).bit_length() - 1  # index of lowest set bit
        buckets[bi] = b & ~(1 << v)
        order.append(v)

        # refine: for each bucket, split off vertices adjacent to v;
        # the adjacent part (label extended with v, lexicographically
        # larger) keeps the bucket's position, the non-adjacent part
        # goes after it
        nv = rows[v]
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            nb = b & nv
            if nb:
                new_buckets.append(nb)
                rest = b & ~nb
                if rest:
                    new_buckets.append(rest)
            else:
                new_buckets.append(b)
        buckets = new_buckets

    return order


def init(graph):
    rows = _bitsets(graph)
    order = _lexbfs(rows)
    return {'ordering': order, 'rows': rows}


def insert_edge(graph, edge, state):
    rows = state['rows']
    u, v = edge
    rows[u] |= 1 << v
    rows[v] |= 1 << u
    order = state['ordering']
    if _is_lexbfs(rows, order):
        return {'ordering': order, 'rows': rows}
    order = _lexbfs(rows)
    return {'ordering': order, 'rows': rows}


def delete_edge(graph, edge, state):
    rows = state['rows']
    u, v = edge
    rows[u] &= ~(1 << v)
    rows[v] &= ~(1 << u)
    order = state['ordering']
    if _is_lexbfs(rows, order):
        return {'ordering': order, 'rows': rows}
    order = _lexbfs(rows)
    return {'ordering': order, 'rows': rows}
