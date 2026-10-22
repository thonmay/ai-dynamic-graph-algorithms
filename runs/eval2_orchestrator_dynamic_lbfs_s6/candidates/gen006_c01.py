"""Dynamic LexBFS ordering (candidate gen006_c01).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n+m), any start vertex, any tie-break.
  * update: try a cheap local repair; if it cannot be certified, fall back to
    a full static recompute.  The fallback guarantees correctness on every
    tested graph and update; the repair path is the attempt to avoid the full
    recompute.

Local repair (the new part vs. the parent):
  A single edge flip (u, v) can only change the LexBFS labels of vertices
  that are "between" u and v in the ordering, because the label of a vertex
  is determined by the set of earlier vertices adjacent to it.  We therefore
  re-derive the ordering on the induced subgraph of the window
  [min(pos[u], pos[v]), max(pos[u], pos[v])] using the same partition-
  refinement scheme, keeping the outside of the window fixed.  The result is
  certified by the (LB) 4-point property; if it fails we fall back.

The (LB) 4-point property (Corneil-Krueger): for all positions a < b < c
with ac in E and ab not in E, there exists d < a with db in E and dc not in
E.  We use it to certify candidate orderings.
"""

# ---------------------------------------------------------------------------
# static LexBFS (partition refinement)
# ---------------------------------------------------------------------------

def _static_lexbfs(n, adj):
    """Return a valid LexBFS ordering of the graph (list of vertices).

    Uses the standard partition-refinement scheme:
      - Start with one bucket containing all vertices.
      - Queue contains that bucket.
      - While queue not empty:
          pop bucket B
          for each v in B (in order):
              output v
              for each other bucket C:
                  split C into C∩N(v) and C\\N(v)
                  if both non-empty, replace C with two buckets, enqueue both
              also split the remainder of B (vertices after v) by N(v);
              if both parts non-empty, enqueue them (N(v) part first).
    """
    if n == 0:
        return []

    from collections import deque

    # Each bucket is a list of vertices.
    # We use a queue of bucket indices to process.
    buckets = [list(range(n))]
    q = deque([0])
    order = []

    while q:
        bi = q.popleft()
        if not buckets[bi]:
            continue
        B = buckets[bi]
        buckets[bi] = []  # mark as consumed
        # rem: the not-yet-output remainder of this bucket, kept as a list.
        # When it is split, the two parts become new buckets and rem is
        # emptied; when not split, rem is carried over unchanged.
        rem = list(B)
        while rem:
            v = rem[0]
            rem = rem[1:]
            order.append(v)
            # Refine all other (non-empty) buckets by N(v).
            for j in range(len(buckets)):
                if j == bi or not buckets[j]:
                    continue
                C = buckets[j]
                in_N = []
                not_N = []
                for w in C:
                    if adj[v][w]:
                        in_N.append(w)
                    else:
                        not_N.append(w)
                if in_N and not_N:
                    # Split bucket j into two.
                    buckets[j] = in_N
                    new_bucket = not_N
                    buckets.append(new_bucket)
                    q.append(j)
                    q.append(len(buckets) - 1)
            # Split the remainder of the current bucket by N(v).
            if rem:
                in_N = [w for w in rem if adj[v][w]]
                not_N = [w for w in rem if not adj[v][w]]
                if in_N and not_N:
                    buckets.append(in_N)
                    buckets.append(not_N)
                    q.append(len(buckets) - 2)
                    q.append(len(buckets) - 1)
                    rem = []
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


# ---------------------------------------------------------------------------
# local repair
# ---------------------------------------------------------------------------

def _try_local_repair(order, adj, edge, is_insert):
    """Try to repair the ordering after a single edge update.

    Returns a new ordering if it can be certified valid, else None.

    The repair re-derives the ordering on the window of the ordering that
    spans the two endpoints of the flipped edge, using the same partition-
    refinement scheme, keeping the outside of the window fixed.  The result
    is certified by the (LB) 4-point property.
    """
    n = len(order)
    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(order):
        pos[vtx] = i

    # Candidate 0: original ordering (maybe still valid)
    if _is_valid_lexbfs(order, adj):
        return list(order)

    if pos[u] == pos[v]:
        return None

    # Window: the contiguous region of the ordering between u and v
    # (inclusive).  A single edge flip can only change the labels of
    # vertices in this region, because the label of a vertex is determined
    # by the set of earlier vertices adjacent to it.
    lo = min(pos[u], pos[v])
    hi = max(pos[u], pos[v])

    # Re-derive the ordering on the induced subgraph of the window.
    # We use the same partition-refinement scheme, but only on the
    # vertices in the window.  The outside of the window is kept fixed.
    window = order[lo:hi + 1]
    k = len(window)
    if k <= 1:
        return None

    # Build a local adjacency matrix for the window.
    # local_adj[i][j] = adj[window[i]][window[j]]
    local_adj = [[0] * k for _ in range(k)]
    for i in range(k):
        wi = window[i]
        for j in range(k):
            local_adj[i][j] = adj[wi][window[j]]

    # Run static LexBFS on the local graph.
    local_order = _static_lexbfs(k, local_adj)

    # Map back to global vertex ids.
    new_window = [window[i] for i in local_order]

    # Build the new global ordering.
    new_order = order[:lo] + new_window + order[hi + 1:]

    # Certify the new ordering.
    if _is_valid_lexbfs(new_order, adj):
        return new_order

    # Candidate 2: shift repair.  Move the later endpoint of the flipped
    # edge to the earliest position where the (LB) 4-point property holds.
    # This is a sound local repair: it only moves one vertex, and the
    # certification guarantees correctness.  It avoids a full recompute
    # whenever the old ordering is "almost" valid after the update.
    later = order[hi]
    rest = order[:hi] + order[hi + 1:]
    for p in range(n):
        cand = rest[:p] + [later] + rest[p:]
        if _is_valid_lexbfs(cand, adj):
            return cand

    # Candidate 3: swap repair.  Swap the two endpoints of the flipped
    # edge.  This is a sound local repair: it only swaps two vertices,
    # and the certification guarantees correctness.  It avoids a full
    # recompute whenever the old ordering is "almost" valid after the
    # update and the two endpoints need to be swapped.
    swap_order = list(order)
    swap_order[lo], swap_order[hi] = swap_order[hi], swap_order[lo]
    if _is_valid_lexbfs(swap_order, adj):
        return swap_order

    return None


# ---------------------------------------------------------------------------
# public interface
# ---------------------------------------------------------------------------

def init(graph):
    n = len(graph)
    order = _static_lexbfs(n, graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    new_order = _try_local_repair(order, graph, edge, True)
    if new_order is None:
        new_order = _static_lexbfs(n, graph)
    return {'ordering': new_order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    new_order = _try_local_repair(order, graph, edge, False)
    if new_order is None:
        new_order = _static_lexbfs(n, graph)
    return {'ordering': new_order, 'n': n}
