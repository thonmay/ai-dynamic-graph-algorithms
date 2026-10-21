"""Dynamic LexBFS ordering.

Strategy:
- init: static partition-refinement LexBFS (label-based, O(n^2)).
- insert_edge / delete_edge: check if the old ordering is still a valid
  LexBFS (4-point property).  If yes, keep it.  If no, try a cheap local
  repair: recompute LexBFS on the suffix of the old ordering (the part
  after the earliest affected position), keeping the prefix fixed.  If
  that fails, fall back to a full recompute.

The 4-point (LB) property: for all positions a < b < c with
ordering[a]~ordering[c] and not ordering[a]~ordering[b],
there exists d < a with ordering[d]~ordering[b] and not ordering[d]~ordering[c].
"""


def _lexbfs(graph):
    """Static LexBFS via label-based approach. Returns ordering list.

    Correct LexBFS: maintain a list of (label, vertex) pairs for the
    remaining vertices, sorted by label (stable, so equal labels keep
    their insertion order).  Repeatedly take the first pair, output the
    vertex, and append 1/0 to every remaining vertex's label according
    to adjacency to the output vertex.  The stable sort preserves the
    FIFO order among vertices with identical labels, which is what
    makes this a BFS (neighbors of the start come before non-neighbors).
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
    """Check the 4-point (LB) property. Returns True if valid."""
    n = len(graph)
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue
            for c in range(b + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue
                # Need d < a with d~b and not d~c
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _suffix_lexbfs(graph, prefix, suffix):
    """Compute a LexBFS ordering of the suffix vertices, given a fixed prefix.

    The prefix is a list of vertices already ordered.  The suffix is a list
    of vertices to order.  We run LexBFS on the suffix, but the initial
    labels are determined by adjacency to the prefix (in prefix order,
    newest first).  This ensures the combined ordering is a valid LexBFS
    if the prefix is a valid LexBFS prefix.

    Returns the full ordering (prefix + new suffix ordering) or None if
    the result is not a valid LexBFS.
    """
    if not suffix:
        return list(prefix)

    # Build adjacency sets for the suffix vertices.
    suffix_set = set(suffix)
    adj = {v: set() for v in suffix}
    for v in suffix:
        for w in suffix:
            if v != w and graph[v][w]:
                adj[v].add(w)

    # Initial labels: adjacency to the prefix, in prefix order (newest first).
    # The prefix is ordered prefix[0], prefix[1], ..., prefix[k-1].
    # The label for a suffix vertex v is the list of bits
    # [graph[v][prefix[k-1]], graph[v][prefix[k-2]], ..., graph[v][prefix[0]]]
    # (newest prefix vertex first).
    labels = {}
    for v in suffix:
        labels[v] = [1 if graph[v][p] else 0 for p in reversed(prefix)]

    remaining = list(suffix)
    ordered_suffix = []

    for _ in range(len(suffix)):
        # Stable sort by label in REVERSE order (newest bit most significant).
        remaining.sort(key=lambda v: labels[v], reverse=True)
        best = remaining[0]
        ordered_suffix.append(best)
        remaining.remove(best)
        for v in remaining:
            labels[v].append(1 if best in adj[v] else 0)

    return list(prefix) + ordered_suffix


def _try_local_repair(graph, ordering, u, v):
    """Try to fix the ordering after an edge update involving (u, v).

    Strategy: find the earliest position where the update could affect
    validity, then recompute LexBFS on the suffix starting at that
    position, keeping the prefix fixed.  Try several candidate split
    points (from the earliest affected position up to a few positions
    later) and return the first valid result.

    Returns a valid ordering or None.
    """
    n = len(graph)
    pos = {v: i for i, v in enumerate(ordering)}
    pu = pos[u]
    pv = pos[v]
    # The earliest position that could be affected is min(pu, pv).
    # But the 4-point property can be violated at any position a where
    # a < b < c and the edge (u,v) is involved.  The earliest possible
    # violation position is 0 (if u or v is at position 0 and the edge
    # change affects the property for some b, c after it).
    #
    # We try split points from 0 up to min(pu, pv) + 2 (a small window).
    # For each split point s, we keep ordering[0:s] as prefix and
    # recompute LexBFS on ordering[s:].
    earliest = min(pu, pv)
    # Try split points from 0 to earliest + 2 (capped at n).
    for s in range(0, min(earliest + 3, n)):
        prefix = ordering[:s]
        suffix = ordering[s:]
        candidate = _suffix_lexbfs(graph, prefix, suffix)
        if candidate is not None and _is_valid_lexbfs(graph, candidate):
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
