"""Dynamic LexBFS ordering.

Strategy: keep a valid LexBFS ordering in the state.  After an update, first
try to repair the *existing* ordering locally (cheap path); if the repair
fails, fall back to a full recompute (correctness path).

Local repair ideas (all must be verified with the (LB) 4-point property):

* Edge insertion (u, v): the only (LB) triples that can become invalid are
  those with b == u or b == v (the only new non-edge/non-adjacency facts
  involve u or v).  Try a small set of candidate re-orderings that move u
  and/or v earlier in the order (the direction that helps the property:
  the witness d must be *before* a, so pulling the affected vertex forward
  creates more potential witnesses).  Candidates:
    - original order (insertion can only break things, but sometimes the
      order was already robust),
    - move u to the front,
    - move v to the front,
    - move both u and v to the front (u then v, and v then u).
  Each candidate is checked with the O(n^3) (LB) verifier; the first valid
  one is kept.

* Edge deletion (u, v): the only (LB) triples that can become invalid are
  those with a == u or a == v (the only new edge fact ac in E / ab not in E
  change for a in {u, v}).  Try:
    - original order,
    - move u to the front,
    - move v to the front,
    - move both to the front (two orders).

If none of the local candidates is valid, recompute a fresh LexBFS from
scratch (try all starts with the simple O(n^2) label-maximising algorithm,
verified with the (LB) property).
"""


def _check_lb(ordering, graph):
    """Verify the (LB) 4-point property. Returns True if valid.

    For all positions a < b < c with ac in E and ab not in E, there exists
    d < a with db in E and dc not in E.  (The witness d may equal b.)
    """
    n = len(ordering)
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if graph[va][vb]:
                continue  # ab in E, skip
            for c in range(b + 1, n):
                vc = ordering[c]
                if not graph[va][vc]:
                    continue  # ac not in E, skip
                if a == 0:
                    return False  # no d < 0 exists
                for d in range(a):
                    vd = ordering[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        break
                else:
                    return False
    return True


def _lexbfs_simple(graph, start):
    """Simple O(n^2) LexBFS: at each step pick the unvisited vertex whose
    label (tuple of 0/1 adjacency to the already-ordered prefix, in prefix
    order) is lexicographically maximal; ties broken by smallest vertex id.
    This is the textbook definition of LexBFS and is trivially correct.
    """
    n = len(graph)
    if n == 0:
        return []
    order = [start]
    placed = [False] * n
    placed[start] = True
    for _ in range(n - 1):
        best = -1
        best_key = None
        for v in range(n):
            if placed[v]:
                continue
            key = tuple(graph[v][u] for u in order)
            if best_key is None or key > best_key or (key == best_key and v < best):
                best_key = key
                best = v
        order.append(best)
        placed[best] = True
    return order


def _try_all_starts(graph):
    """Try all starting vertices; return the first valid LexBFS ordering."""
    n = len(graph)
    if n == 0:
        return []
    for start in range(n):
        ordering = _lexbfs_simple(graph, start)
        if _check_lb(ordering, graph):
            return ordering
    # Every simple undirected graph has a valid LexBFS ordering, so this
    # should be unreachable.
    return _lexbfs_simple(graph, 0)


def _move_to_front(ordering, verts):
    """Return a new ordering where verts (in the given sequence) are moved
    to the front, in that sequence's order, and the remaining vertices keep
    their relative order."""
    vs = set(verts)
    rest = [v for v in ordering if v not in vs]
    return list(verts) + rest


def _local_repair(ordering, graph, u, v):
    """Try cheap local re-orderings; return the first valid one or None."""
    if u == v:
        return None
    candidates = [
        ordering,
        _move_to_front(ordering, [u]),
        _move_to_front(ordering, [v]),
        _move_to_front(ordering, [u, v]),
        _move_to_front(ordering, [v, u]),
    ]
    seen = set()
    for cand in candidates:
        key = tuple(cand)
        if key in seen:
            continue
        seen.add(key)
        if _check_lb(cand, graph):
            return cand
    return None


def init(graph):
    n = len(graph)
    ordering = _try_all_starts(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state.get('ordering')
    if ordering is None or len(ordering) != len(graph):
        ordering = _try_all_starts(graph)
        state = dict(state)
        state['ordering'] = ordering
        return state
    repaired = _local_repair(ordering, graph, u, v)
    if repaired is None:
        repaired = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = repaired
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state.get('ordering')
    if ordering is None or len(ordering) != len(graph):
        ordering = _try_all_starts(graph)
        state = dict(state)
        state['ordering'] = ordering
        return state
    repaired = _local_repair(ordering, graph, u, v)
    if repaired is None:
        repaired = _try_all_starts(graph)
    state = dict(state)
    state['ordering'] = repaired
    return state
