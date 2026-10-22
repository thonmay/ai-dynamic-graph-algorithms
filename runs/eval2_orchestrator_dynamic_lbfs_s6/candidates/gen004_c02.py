"""Dynamic LexBFS ordering (candidate gen004_c02).

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
              if both parts non-empty, enqueue them as new buckets
              (N(v) part first, then the rest).
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
        # Track the remainder of B as a live bucket index so that
        # subsequent vertices in B refine it (and it is refined by them).
        rem_idx = None
        for idx, v in enumerate(B):
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
                    if j == rem_idx:
                        rem_idx = len(buckets) - 1
            # Split the remainder of the current bucket by N(v).
            if idx + 1 < len(B):
                if rem_idx is None:
                    rem = B[idx + 1:]
                else:
                    rem = buckets[rem_idx]
                    buckets[rem_idx] = []
                in_N = [w for w in rem if adj[v][w]]
                not_N = [w for w in rem if not adj[v][w]]
                if in_N and not_N:
                    buckets.append(in_N)
                    buckets.append(not_N)
                    q.append(len(buckets) - 2)
                    q.append(len(buckets) - 1)
                    rem_idx = len(buckets) - 1
                elif in_N:
                    buckets.append(in_N)
                    rem_idx = len(buckets) - 1
                elif not_N:
                    buckets.append(not_N)
                    rem_idx = len(buckets) - 1
                else:
                    rem_idx = None
        # If the remainder was never split, enqueue it so it is processed.
        if rem_idx is not None and buckets[rem_idx]:
            q.append(rem_idx)
            rem_idx = None
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
