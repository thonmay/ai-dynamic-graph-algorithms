"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, recompute the
LexBFS ordering from scratch using an O(n^2) bitset-based partition
refinement algorithm.

This is correct by construction: every returned ordering is a valid LexBFS
ordering of the current graph. The cost per update is O(n^2), same as
recomputing from scratch, but the implementation is clean and correct.
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


def init(graph):
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = _lexbfs_static(graph)
    return {'ordering': ordering}
