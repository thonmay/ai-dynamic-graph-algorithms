"""Dynamic LexBFS ordering.

Strategy:
- init: static partition-refinement LexBFS (label-based, O(n^2)).
- insert_edge / delete_edge: check if the old ordering is still a valid
  LexBFS using the 4-point (LB) property with bitset adjacency.  If yes,
  keep it.  If no, try a cheap local repair (move one of the endpoints to
  a different position, or swap them).  If that fails, fall back to a
  full recompute.

The 4-point (LB) property: for all positions a < b < c with
ordering[a]~ordering[c] and not ordering[a]~ordering[b],
there exists d < a with ordering[d]~ordering[b] and not ordering[d]~ordering[c].
"""


def _lexbfs(graph):
    """Static LexBFS via label-based approach. Returns ordering list.

    Maintain a list of (label, vertex) pairs for the remaining vertices,
    sorted by label (stable, so equal labels keep their insertion order).
    Repeatedly take the first pair, output the vertex, and append 1/0 to
    every remaining vertex's label according to adjacency to the output
    vertex.  The stable sort preserves the FIFO order among vertices with
    identical labels, which is what makes this a BFS (neighbors of the
    start come before non-neighbors).
    """
    n = len(graph)
    adj = [set() for _ in range(n)]
    for v in range(n):
        for w in range(v + 1, n):
            if graph[v][w]:
                adj[v].add(w)
                adj[w].add(v)

    ordered = []
    remaining = list(range(n))
    labels = {v: [] for v in range(n)}

    for _ in range(n):
        # Stable sort by label in REVERSE order: a vertex with label [1,...]
        # (adjacent to the most recently selected vertex) comes before one
        # with [0,...].  Equal labels keep their current order (FIFO).
        # This ensures neighbors of the start are output before non-neighbors.
        remaining.sort(key=lambda v: labels[v], reverse=True)
        best = remaining[0]
        ordered.append(best)
        remaining.remove(best)
        for v in remaining:
            # Append the adjacency bit to the most recently selected vertex.
            # The label is the adjacency vector to the ordered prefix, in
            # selection order (newest first).  The reverse sort makes the
            # newest bit the most significant, so neighbors of the most
            # recently selected vertex come first.
            labels[v].append(1 if best in adj[v] else 0)

    return ordered


def _is_valid_lexbfs(graph, ordering):
    """Check the 4-point (LB) property using bitsets. Returns True if valid.

    For all a < b < c with a~c and not a~b, there must exist d < a with
    d~b and not d~c.

    We iterate over (a, b) pairs where not a~b, compute the set of
    candidate d's (vertices before a that are adjacent to b), and then
    check that for every c > b with a~c, at least one candidate d is
    not adjacent to c.
    """
    n = len(graph)
    # Build bitsets: adj_bits[v] is an int with bit w set iff v~w
    adj_bits = [0] * n
    for v in range(n):
        bits = 0
        row = graph[v]
        for w in range(n):
            if row[w]:
                bits |= (1 << w)
        adj_bits[v] = bits

    # Precompute prefix bitsets: prefix[a] = bitset of vertices in ordering[0..a-1]
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | (1 << ordering[i])

    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue
            # d must be in prefix[a] and d~vb
            d_candidates = prefix[a] & adj_bits[vb]
            if d_candidates == 0:
                # No d < a adjacent to vb, so any c > b with va~vc fails
                for c in range(b + 1, n):
                    if graph[va][ordering[c]]:
                        return False
                continue
            # For each c > b with va~vc, need d_candidates & ~adj_bits[vc] != 0
            for c in range(b + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue
                if (d_candidates & ~adj_bits[vc]) == 0:
                    return False
    return True


def _try_local_repair(graph, ordering, u, v):
    """Try to fix the ordering after an edge update involving (u, v).

    Try moving u or v to various positions, or swapping them.
    Returns a valid ordering or None.
    """
    n = len(graph)

    # Try moving u to each position
    for new_pos in range(n):
        candidate = [x for x in ordering if x != u]
        candidate.insert(new_pos, u)
        if _is_valid_lexbfs(graph, candidate):
            return candidate

    # Try moving v to each position
    for new_pos in range(n):
        candidate = [x for x in ordering if x != v]
        candidate.insert(new_pos, v)
        if _is_valid_lexbfs(graph, candidate):
            return candidate

    # Try swapping u and v
    candidate = list(ordering)
    iu = candidate.index(u)
    iv = candidate.index(v)
    candidate[iu], candidate[iv] = candidate[iv], candidate[iu]
    if _is_valid_lexbfs(graph, candidate):
        return candidate

    return None


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    repaired = _try_local_repair(graph, ordering, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    return {'ordering': _lexbfs(graph)}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    repaired = _try_local_repair(graph, ordering, u, v)
    if repaired is not None:
        return {'ordering': repaired}
    return {'ordering': _lexbfs(graph)}
