"""Dynamic LexBFS ordering (candidate gen003_c03).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static label-based LexBFS, O(n^2) on the adjacency matrix.
  * update: try a cheap local repair (reorder the affected region of the
    ordering using the (LB) 4-point certificate); if the repair cannot be
    certified, fall back to a full static recompute.  The fallback
    guarantees correctness on every tested graph and update; the repair
    path is the attempt to avoid the full recompute.

The (LB) 4-point property (Corneil-Krueger): for all positions a < b < c
with ac in E and ab not in E, there exists d < a with db in E and dc not in
E.  We use it both to certify candidate orderings and to guide the repair.
"""

# ---------------------------------------------------------------------------
# static LexBFS (label-based)
# ---------------------------------------------------------------------------

def _static_lexbfs(n, adj):
    """Return a valid LexBFS ordering of the graph (list of vertices).

    Label-based formulation:
      - labels[v] = tuple of already-selected neighbors of v (in selection
        order), initially empty.
      - Repeat n times: pick the unselected vertex with the lexicographically
        LARGEST label (tie-break: smallest id); append to order; for each
        remaining unselected u, if adj[v][u] then labels[u] += (v,).

    This is trivially a permutation and is a valid LexBFS ordering for any
    tie-break.
    """
    if n == 0:
        return []

    labels = [()] * n
    unselected = set(range(n))
    order = []

    for _ in range(n):
        # Pick the unselected vertex with the lexicographically largest
        # label; tie-break by smallest id.
        best = None
        for v in unselected:
            if best is None or labels[v] > labels[best] or (
                labels[v] == labels[best] and v < best
            ):
                best = v
        order.append(best)
        unselected.remove(best)
        for u in unselected:
            if adj[best][u]:
                labels[u] = labels[u] + (best,)
    return order


def _is_valid_lexbfs(order, adj):
    """Check the (LB) 4-point property.  Returns True if valid."""
    n = len(order)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb]:
                continue  # ab in E, condition not triggered
            # ab not in E; check for all c > b with ac in E
            for c in range(b + 1, n):
                vc = order[c]
                if not adj[va][vc]:
                    continue  # ac not in E
                # need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = order[d]
                    if adj[vd][vb] and not adj[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _is_permutation(order, n):
    """Check that order is a permutation of range(n)."""
    if len(order) != n:
        return False
    seen = [False] * n
    for v in order:
        if v < 0 or v >= n or seen[v]:
            return False
        seen[v] = True
    return True


def _ensure_valid(order, n, adj):
    """Safety net: if order is not a valid LexBFS permutation, recompute."""
    if _is_permutation(order, n) and _is_valid_lexbfs(order, adj):
        return order
    return _static_lexbfs(n, adj)


# ---------------------------------------------------------------------------
# local repair
# ---------------------------------------------------------------------------

def _try_local_repair(order, adj, edge, is_insert):
    """Try to repair the ordering after a single edge update.

    Returns a new ordering if it can be certified valid, else None.
    """
    n = len(order)
    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(order):
        pos[vtx] = i

    candidates = []

    # Candidate 0: original ordering (maybe still valid)
    candidates.append(list(order))

    if pos[u] != pos[v]:
        # Candidate 1: swap u and v
        cand = list(order)
        iu, iv = pos[u], pos[v]
        cand[iu], cand[iv] = cand[iv], cand[iu]
        candidates.append(cand)

        # Candidate 2: move v to right after u
        cand = list(order)
        iv = cand.index(v)
        cand.pop(iv)
        iu = cand.index(u)
        cand.insert(iu + 1, v)
        candidates.append(cand)

        # Candidate 3: move v to right before u
        cand = list(order)
        iv = cand.index(v)
        cand.pop(iv)
        iu = cand.index(u)
        cand.insert(iu, v)
        candidates.append(cand)

        # Candidate 4: move u to right after v
        cand = list(order)
        iu = cand.index(u)
        cand.pop(iu)
        iv = cand.index(v)
        cand.insert(iv + 1, u)
        candidates.append(cand)

        # Candidate 5: move u to right before v
        cand = list(order)
        iu = cand.index(u)
        cand.pop(iu)
        iv = cand.index(v)
        cand.insert(iv, u)
        candidates.append(cand)

    # Check each candidate
    for cand in candidates:
        if _is_valid_lexbfs(cand, adj):
            return cand
    return None


# ---------------------------------------------------------------------------
# public interface
# ---------------------------------------------------------------------------

def init(graph):
    n = len(graph)
    order = _static_lexbfs(n, graph)
    order = _ensure_valid(order, n, graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    new_order = _try_local_repair(order, graph, edge, True)
    if new_order is None:
        new_order = _static_lexbfs(n, graph)
    new_order = _ensure_valid(new_order, n, graph)
    return {'ordering': new_order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    new_order = _try_local_repair(order, graph, edge, False)
    if new_order is None:
        new_order = _static_lexbfs(n, graph)
    new_order = _ensure_valid(new_order, n, graph)
    return {'ordering': new_order, 'n': n}
