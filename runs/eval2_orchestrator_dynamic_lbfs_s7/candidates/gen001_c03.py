"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a valid LexBFS ordering under single edge flips.

Correctness core: the (LB) 4-point property of Corneil-Krueger certifies
that an ordering is a LexBFS ordering.  After an update we try to repair
the ordering locally (cheap); if the local repair cannot certify validity
we fall back to a full O(n^2) partition-refinement LexBFS recompute, which
is always correct.

Local repair idea:
- Insertion of edge (u,v): the only 4-point violations an insertion can
  create are of the form (a=u, b, c=v) or (a=v, b, c=u) with a<b<c.
  For each such b we need some d<a with db in E and dc not in E.  If none
  exists, moving b earlier (before a) removes the violation; we then
  re-check.  This is a bounded local fix.
- Deletion of edge (u,v): the only violations a deletion can create are
  (a=u, b, c=v) or (a=v, b, c=u) where the witnessing d used to be the
  deleted edge's endpoint... actually the witness d must satisfy db in E
  and dc not in E; deleting (u,v) can only break a witness when the
  witness edge was (u,v) itself, i.e. d=u or d=v with the other being b
  or c.  In the violation (a=u,b,c=v) the witness d<a has db in E and
  dc not in E; the deleted edge (u,v) is not db or dc unless d==v (impossible,
  d<a=u) ... so deletion of (u,v) can only create violations where the
  witness edge was (u,v): that requires {d,b}={u,v} or {d,c}={u,v}.
  We handle it by checking all potential violations involving u or v and
  repairing by moving b earlier if needed.

To keep things simple and correct, after any update we:
1. Run a local repair pass (bounded moves).
2. Verify the full 4-point property in O(n^2) using bitsets.
3. If verification fails, recompute LexBFS from scratch (O(n^2) with
   bitsets) and store it.

This guarantees correctness on every update; the recompute is the
fallback, and the local repair often avoids it.
"""

def _n_of(graph):
    return len(graph)


def _bitsets(graph):
    """Adjacency as Python ints (bit i = neighbor i)."""
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


def _lexbfs(adj, n):
    """Partition-refinement LexBFS with bitsets.  Returns ordering list.

    Uses the standard algorithm: maintain an ordered list of buckets
    (each a set of unprocessed vertices).  When processing vertex v,
    split each bucket by adjacency to v (neighbors first).  Pick the
    first vertex from the first non-empty bucket.
    """
    if n == 0:
        return []
    start = 0
    order = [start]
    # buckets: list of sets; initially one bucket with all remaining vertices
    buckets = [set(range(1, n))]
    for v in order:
        av = adj[v]
        new_buckets = []
        for b in buckets:
            if not b:
                continue
            # split b into b & N(v) and b & ~N(v)
            inside = set(x for x in b if (av >> x) & 1)
            outside = b - inside
            if inside:
                new_buckets.append(inside)
            if outside:
                new_buckets.append(outside)
        buckets = new_buckets
        # pick the first vertex from the first non-empty bucket
        for b in buckets:
            if b:
                w = min(b)
                b.discard(w)
                order.append(w)
                break
    return order


def _verify(order, adj, n):
    """Check the (LB) 4-point property.

    For all a < b < c (positions) with ac in E and ab not in E,
    exists d < a with db in E and dc not in E.

    O(n^3) worst case with bitsets; acceptable for verification.
    """
    for pa in range(n):
        a = order[pa]
        A = adj[a]
        for pb in range(pa + 1, n):
            b = order[pb]
            if (A >> b) & 1:
                continue  # ab in E: no constraint
            # C = neighbors of a at positions > pb
            C = A & ~((1 << (pb + 1)) - 1)
            if not C:
                continue
            # W = neighbors of b at positions < pa (candidates for d)
            W = adj[b] & ((1 << pa) - 1)
            if not W:
                return False  # no d < a adjacent to b, but C non-empty
            # Need: exists c in C such that W is NOT a subset of N(c)
            # i.e. exists c in C with W & ~N(c) != 0
            found = False
            c_bits = C
            while c_bits:
                lb = c_bits & (-c_bits)
                c = lb.bit_length() - 1
                c_bits ^= lb
                if W & ~adj[c]:
                    found = True
                    break
            if not found:
                return False
    return True


def _recompute(graph):
    n = _n_of(graph)
    adj = _bitsets(graph)
    order = _lexbfs(adj, n)
    return {'ordering': order, 'adj': adj, 'n': n}


def init(graph):
    return _recompute(graph)


def _try_local_repair(order, adj, n, u, v, inserted):
    """Try to repair the ordering after flipping edge (u,v).

    Returns a new ordering if the local repair succeeds (verified),
    else None.
    """
    order = list(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i

    # Update adj for the flipped edge.
    if inserted:
        adj[u] |= (1 << v)
        adj[v] |= (1 << u)
    else:
        adj[u] &= ~(1 << v)
        adj[v] &= ~(1 << u)

    # Local repair: repeatedly find a 4-point violation and fix it by
    # moving b earlier.  Bound the number of moves to avoid infinite loops.
    #
    # After a single edge flip, the only NEW violations involve u or v
    # as 'a' or 'c'.  Moving b earlier can create new violations where b
    # is now 'a' or 'c'.  We track all moved vertices and check them too.
    #
    # The scan is O(|cand| * n^2) per iteration.  In practice |cand| is
    # small (a few vertices) and the number of iterations is bounded.
    max_moves = 4 * n
    moves = 0
    moved = set()
    while moves < max_moves:
        # Candidate set for 'a': u, v, and all moved vertices.
        cand = {u, v} | moved
        violation = None
        for a in cand:
            pa = pos[a]
            A = adj[a]
            for pb in range(pa + 1, n):
                b = order[pb]
                if (A >> b) & 1:
                    continue  # ab in E
                # need c > b with ac in E
                C = A & ~((1 << (pb + 1)) - 1)  # neighbors of a after position pb
                if not C:
                    continue
                # check: for all c in C, exists d < a with db in E and dc not in E
                # i.e. NOT (exists c in C such that N(b) & prefix(pa) subset of N(c))
                W = adj[b] & ((1 << pa) - 1)
                if not W:
                    # no d < a adjacent to b: violation if C non-empty
                    violation = (a, b)
                    break
                # check if W is subset of N(c) for some c in C
                bad = False
                c_bits = C
                while c_bits:
                    lb = c_bits & (-c_bits)
                    c = lb.bit_length() - 1
                    c_bits ^= lb
                    if W & ~adj[c]:
                        # exists d in W not adjacent to c: witness found
                        continue
                    # W subset of N(c): no witness for this c
                    bad = True
                    break
                if bad:
                    violation = (a, b)
                    break
            if violation:
                break
        if not violation:
            break
        a, b = violation
        # Move b to just before a.
        pa = pos[a]
        order.remove(b)
        order.insert(pa, b)
        moved.add(b)
        moves += 1
    else:
        return None

    # Verify the repaired ordering.
    if _verify(order, adj, n):
        return order
    return None


def insert_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = list(state['adj'])
    order = state['ordering']
    new_order = _try_local_repair(order, adj, n, u, v, True)
    if new_order is None:
        # Full recompute.
        return _recompute(graph)
    return {'ordering': new_order, 'adj': adj, 'n': n}


def delete_edge(graph, edge, state):
    u, v = edge
    n = state['n']
    adj = list(state['adj'])
    order = state['ordering']
    new_order = _try_local_repair(order, adj, n, u, v, False)
    if new_order is None:
        return _recompute(graph)
    return {'ordering': new_order, 'adj': adj, 'n': n}
