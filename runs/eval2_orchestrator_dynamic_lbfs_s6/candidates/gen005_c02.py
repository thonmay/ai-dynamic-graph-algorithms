"""Dynamic LexBFS ordering (candidate gen005_c02).

Strategy: maintain a valid LexBFS ordering under single-edge updates.

Correctness core:
  * init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n+m), any start vertex, any tie-break.
  * update: try a cheap local repair; if the repair cannot be certified,
    fall back to a full static recompute.  The fallback guarantees
    correctness on every tested graph and update; the repair path is the
    attempt to avoid the full recompute.

Local repair (the improvement over the parent):
  The only vertices whose LexBFS labels can change after flipping edge
  (u, v) are u, v and their neighbors (their labels differ from the old
  ones only in the bit for the other endpoint).  We therefore recompute a
  LexBFS ordering of the induced subgraph on the affected region
      R = {u, v} ∪ N(u) ∪ N(v)
  (which is small in sparse graphs), splice it back into the old ordering
  in place of the span [min(pos[u],pos[v]), max(pos[u],pos[v])], and
  certify the result with the (LB) 4-point property of Corneil-Krueger.
  If certification fails we fall back to a full recompute, so correctness
  is never at risk.

The (LB) 4-point property: for all positions a < b < c with ac in E and
ab not in E, there exists d < a with db in E and dc not in E.
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

def _try_local_repair(order, adj, edge):
    """Try to repair the ordering after a single edge update.

    Returns a new ordering if it can be certified valid, else None.
    """
    n = len(order)
    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(order):
        pos[vtx] = i

    # Candidate 0: original ordering (maybe still valid).
    if _is_valid_lexbfs(order, adj):
        return list(order)

    if pos[u] == pos[v]:
        return None

    # Affected region: u, v and their neighbors.
    region = set()
    region.add(u)
    region.add(v)
    row_u = adj[u]
    row_v = adj[v]
    for w in range(n):
        if row_u[w] or row_v[w]:
            region.add(w)

    # The span of the old ordering that we will replace.
    lo = min(pos[u], pos[v])
    hi = max(pos[u], pos[v])
    span = order[lo:hi + 1]
    # Vertices of the region that lie inside the span (the rest of the
    # region, if any, stays where it is).
    in_span = [x for x in span if x in region]
    # Vertices of the span that are not in the region keep their relative
    # order; we interleave the new region ordering among them.

    # Recompute a LexBFS ordering of the induced subgraph on the region.
    # The subgraph is induced, so its LexBFS ordering is a valid relative
    # ordering of the region in the full graph (labels restricted to the
    # region are exactly the subgraph labels).
    rlist = sorted(region)
    m = len(rlist)
    sub_adj = [[0] * m for _ in range(m)]
    for i, x in enumerate(rlist):
        row = adj[x]
        si = sub_adj[i]
        for j, y in enumerate(rlist):
            if row[y]:
                si[j] = 1
    sub_order = _static_lexbfs(m, sub_adj)
    new_region = [rlist[i] for i in sub_order]

    # The splice below preserves the relative order of the region vertices
    # that were OUTSIDE the span (they stay put).  For the candidate to be
    # a valid full-graph LexBFS ordering, the new relative order of the
    # region must therefore agree with the old one on those vertices.
    # (If it does not, the splice would reorder them and the certificate
    # would catch it, but checking here avoids building a doomed candidate.)
    old_rel = [x for x in order if x in region]
    new_rel = [x for x in new_region if x in region]
    if old_rel != new_rel:
        return None

    # Splice: walk the span; where a vertex is in the region, take the next
    # vertex from new_region (in its new relative order); otherwise keep it.
    # This preserves the relative order of non-region vertices and of
    # region vertices that were outside the span (they are untouched).
    it = iter(new_region)
    nxt = next(it, None)
    spliced = []
    for x in span:
        if x in region:
            spliced.append(nxt)
            nxt = next(it, None)
        else:
            spliced.append(x)

    cand = order[:lo] + spliced + order[hi + 1:]
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
    new_order = _try_local_repair(order, graph, edge)
    if new_order is None:
        new_order = _static_lexbfs(n, graph)
    return {'ordering': new_order, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    order = state['ordering']
    new_order = _try_local_repair(order, graph, edge)
    if new_order is None:
        new_order = _static_lexbfs(n, graph)
    return {'ordering': new_order, 'n': n}
