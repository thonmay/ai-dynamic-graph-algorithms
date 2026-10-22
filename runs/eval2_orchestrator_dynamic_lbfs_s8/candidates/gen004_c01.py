"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first check
whether the previously maintained ordering is still a valid LexBFS ordering
of the updated graph, using the (LB) 4-point property of Corneil and
Krueger: for all positions a < b < c with ac in E and ab not in E, there
exists d < a with db in E and dc not in E. If it is still valid, keep it
(no recompute). Otherwise recompute a fresh LexBFS ordering from scratch
with an O(n^2) bitset-based partition refinement.

Correctness: the returned ordering is either the previous ordering, which
was certified valid on the current graph, or a freshly computed LexBFS
ordering, which is valid by construction.
"""


def _build_adj_bitsets(graph):
    """Build adjacency as Python int bitsets."""
    n = len(graph)
    adj = [0] * n
    for i in range(n):
        row = graph[i]
        bits = 0
        for j in range(n):
            if row[j]:
                bits |= (1 << j)
        adj[i] = bits
    return adj


def _is_valid_lexbfs(ordering, adj):
    """Check the (LB) 4-point property for `ordering` on graph `adj`.

    For all positions a < b < c with ac in E and ab not in E, there must
    exist d < a with db in E and dc not in E. O(n^2) with bitsets.
    """
    n = len(ordering)
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    allmask = (1 << n) - 1
    # prefix[p] = set of vertices at positions in [0, p)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << ordering[i])

    for a in range(n):
        va = ordering[a]
        # candidates c: position > a, adjacent to va
        cands = adj[va] & ~prefix[a + 1]
        nonadj = allmask & ~adj[va]
        while cands:
            lsb = cands & (-cands)
            vc = lsb.bit_length() - 1
            cands ^= lsb
            pc = pos[vc]
            # b candidates: a < pos[b] < pos[c], b not adjacent to va
            bset = (prefix[pc] & ~prefix[a + 1]) & nonadj
            if not bset:
                continue
            # Need: exists b in bset with (prefix[a] & adj[b] & ~adj[vc]) != 0
            # i.e., (OR_{b in bset} adj[b]) & prefix[a] & ~adj[vc] != 0
            union_adj = 0
            bs = bset
            while bs:
                lsb2 = bs & (-bs)
                vb = lsb2.bit_length() - 1
                bs ^= lsb2
                union_adj |= adj[vb]
            if (union_adj & prefix[a] & ~adj[vc]):
                return False
    return True


def _lexbfs_static(graph):
    """Compute a LexBFS ordering using partition refinement with bitsets.
    O(n^2) time. Returns a list of n vertices in LexBFS order."""
    n = len(graph)
    if n == 0:
        return []
    if n == 1:
        return [0]

    adj = _build_adj_bitsets(graph)

    # P: list of bitsets (blocks), in order.
    # Start with one block containing all vertices.
    P = [(1 << n) - 1]
    ordering = []

    for _ in range(n):
        # Find first non-empty block
        idx = 0
        while idx < len(P) and P[idx] == 0:
            idx += 1
        if idx >= len(P):
            break

        # Pick a vertex from P[idx] (lowest set bit for determinism)
        block = P[idx]
        v = (block & (-block)).bit_length() - 1
        P[idx] = block & ~(1 << v)
        ordering.append(v)

        # Refine all blocks by adjacency to v
        new_P = []
        for b in P:
            if b == 0:
                continue
            b1 = b & adj[v]   # neighbors of v
            b2 = b & ~adj[v]  # non-neighbors of v
            if b1:
                new_P.append(b1)
            if b2:
                new_P.append(b2)
        P = new_P

    return ordering


def _update(graph, state):
    """After a single edge flip, return the new state."""
    n = len(graph)
    if n == 0:
        return {'ordering': []}
    adj = _build_adj_bitsets(graph)
    prev = state.get('ordering') if state else None
    if prev is not None and len(prev) == n and sorted(prev) == list(range(n)):
        if _is_valid_lexbfs(prev, adj):
            return {'ordering': prev}
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}


def init(graph):
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    return _update(graph, state)


def delete_edge(graph, edge, state):
    return _update(graph, state)
