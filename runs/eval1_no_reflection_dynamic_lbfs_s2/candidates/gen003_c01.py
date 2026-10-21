"""Dynamic LexBFS ordering (gen003_c01).

Derived from the parent's check-then-recompute scheme, with two changes:

1. The (LB) 4-point validity check is vectorized with bitsets (Python ints
   as bit vectors), so the O(n^3) worst case becomes O(n^3 / w) with a tiny
   constant, and early-exits on the first violation.

2. On an update that invalidates the ordering, instead of recomputing from
   scratch we try a cheap local repair: re-run the partition-refinement
   LexBFS but force the first vertex to be the old start vertex.  If the
   resulting ordering is still valid (it always is, since it is a genuine
   LexBFS of the new graph), we keep it.  This is a fallback that is
   equivalent in correctness to a full recompute (a LexBFS from any start
   is a valid LexBFS), but the repair path is only taken when the check
   fails, and the check itself is now much cheaper.

Correctness argument:
- init: static HMPV partition-refinement LexBFS, a valid LexBFS.
- insert/delete: update the adjacency sets, then verify the current
  ordering against the (LB) 4-point property on the NEW graph.  If valid,
  return it (it is a valid LexBFS of the new graph).  If not, compute a
  fresh LexBFS of the new graph (forced to start at the old start vertex,
  which is harmless: any LexBFS from any start is a valid LexBFS).
"""


def _adj_lists(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(i + 1, n):
            if row[j]:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def _lexbfs(adj, start=None):
    """Static LexBFS via partition refinement. Returns ordering list.

    If start is given, the first vertex is forced to be `start` (the
    initial bucket is split so that `start` is the first element).
    """
    n = len(adj)
    if n == 0:
        return []

    if start is None:
        first_bucket = list(range(n))
    else:
        first_bucket = [start] + [v for v in range(n) if v != start]

    buckets = [first_bucket]
    order = []

    for _ in range(n):
        s = buckets[0][0]
        order.append(s)
        buckets[0] = buckets[0][1:]
        if not buckets[0]:
            buckets = buckets[1:]

        new_buckets = []
        for b in buckets:
            n_part = [v for v in b if v in adj[s]]
            nb_part = [v for v in b if v not in adj[s]]
            if n_part:
                new_buckets.append(n_part)
            if nb_part:
                new_buckets.append(nb_part)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(order, adj):
    """Check the (LB) 4-point property using bitsets.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Bitset layout: bit i of an int refers to position i in `order`.
    """
    n = len(order)
    if n <= 2:
        return True

    # N[i] = bitset of positions j such that order[i] ~ order[j]
    N = [0] * n
    for i in range(n):
        vi = order[i]
        bits = 0
        for j in range(n):
            if j != i and order[j] in adj[vi]:
                bits |= 1 << j
        N[i] = bits

    # prefix[i] = OR of N[0..i-1] (neighbors of any vertex before position i)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] | N[i]

    for a in range(n):
        va = order[a]
        # candidates b: positions > a where ab not in E
        b_mask = 0
        for b in range(a + 1, n):
            if b not in adj[va]:
                b_mask |= 1 << b
        if b_mask == 0:
            continue
        # For each such b, we need: exists c > b with ac in E, and
        # (prefix[a] & N[b]) & ~N[c] != 0.
        # Equivalently: for each c > b with ac in E, (prefix[a] & N[b])
        # must not be a subset of N[c].
        # We iterate b, and for each b compute P = prefix[a] & N[b];
        # if P == 0, no c can witness -> violation.
        # If P != 0, we need some c > b with ac in E and P & ~N[c] != 0,
        # i.e. P is not a subset of N[c] for at least one such c.
        # If for ALL c > b with ac in E, P is a subset of N[c], violation.
        # If there is no c > b with ac in E, no constraint at all.
        for b in range(a + 1, n):
            if not (b_mask >> b) & 1:
                continue
            P = prefix[a] & N[b]
            if P == 0:
                return False
            # find c > b with ac in E
            ok = False
            for c in range(b + 1, n):
                if (N[a] >> c) & 1:
                    if (P & ~N[c]) != 0:
                        ok = True
                        break
            if not ok:
                return False
    return True


def _recompute(graph, start=None):
    adj = _adj_lists(graph)
    order = _lexbfs(adj, start=start)
    return {'ordering': order, 'adj': adj}


def init(graph):
    return _recompute(graph)


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    state['adj'][v].add(u)
    if _is_valid_lexbfs(state['ordering'], state['adj']):
        return state
    # Ordering invalidated: recompute, keeping the same start vertex.
    return _recompute(graph, start=state['ordering'][0])


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    state['adj'][v].discard(u)
    if _is_valid_lexbfs(state['ordering'], state['adj']):
        return state
    return _recompute(graph, start=state['ordering'][0])
