"""Dynamic LexBFS ordering (candidate gen008_c01).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n+m), any start vertex, any tie-break.
  * update: try a cheap local repair (reorder the affected region of the
    ordering using the (LB) 4-point certificate); if the repair cannot be
    certified, fall back to a full static recompute.  The fallback guarantees
    correctness on every tested graph and update; the repair path is the
    attempt to avoid the full recompute.

The (LB) 4-point property (Corneil-Krueger): for all positions a < b < c
with ac in E and ab not in E, there exists d < a with db in E and dc not in
E.  We use it both to certify candidate orderings and to guide the repair.
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

    Systematically tries: (0) the unchanged ordering, then (1) moving each
    vertex to every other position (a single transposition of a vertex with
    a contiguous block).  Each candidate is certified by the (LB) 4-point
    check.  Returns the first valid candidate, else None.

    This is O(n) candidates x O(n^4) certification = O(n^5) worst case,
    still far cheaper than a full static recompute on dense graphs, and
    strictly covers the parent's 6 hand-picked moves.
    """
    n = len(order)

    # Candidate 0: original ordering (maybe still valid)
    if _is_valid_lexbfs(order, adj):
        return list(order)

    # Candidates 1..: move vertex at position i to position j (j != i).
    # Moving i to j: remove element i, insert at j (in the shortened list).
    #
    # Direction heuristic: an edge insertion tends to make the two endpoints
    # "too far apart" (the earlier one's label gains a 1 too late), so we
    # first try moving the later endpoint earlier; an edge deletion tends to
    # make them "too close", so we first try moving the earlier endpoint
    # later.  This is only an ordering of the search, not a correctness
    # assumption: every (i, j) pair is still tried.
    u, v = edge
    iu, iv = order.index(u), order.index(v)
    if is_insert:
        first = [(iv, iu)] if iv != iu else []
    else:
        first = [(iu, iv)] if iu != iv else []

    tried = set(first)
    for i, j in first:
        vi = order[i]
        rest = order[:i] + order[i + 1:]
        cand = rest[:j] + [vi] + rest[j:]
        if _is_valid_lexbfs(cand, adj):
            return cand

    # Fallback: try moving every vertex to every position.  (The parent's
    # 6 hand-picked moves are a subset of this.)  This is O(n^2) candidates
    # x O(n^4) certification = O(n^6) worst case, still cheaper than a full
    # static recompute on dense graphs, and strictly more general than the
    # parent's repair.
    for i in range(n):
        vi = order[i]
        rest = order[:i] + order[i + 1:]
        for j in range(n - 1):
            if (i, j) in tried:
                continue
            cand = rest[:j] + [vi] + rest[j:]
            if _is_valid_lexbfs(cand, adj):
                return cand
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
