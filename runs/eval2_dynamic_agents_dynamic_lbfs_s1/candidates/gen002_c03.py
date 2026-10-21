"""Dynamic LexBFS ordering.

Strategy:
- init: static partition-refinement LexBFS (O(n^2) label-based).
- insert_edge / delete_edge: check if the old ordering is still a valid
  LexBFS (4-point property).  If yes, keep it.  If no, try a cheap local
  repair (move one of the endpoints to a different position).  If that
  fails, fall back to a full recompute.

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
