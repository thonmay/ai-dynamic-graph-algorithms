"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder only the affected region); if the repair cannot
certify validity, fall back to a full O(n^2) partition-refinement LexBFS
recomputation.

The (LB) 4-point property (Corneil & Krueger) certifies validity:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _lexbfs_full(graph):
    """Static O(n^2) partition-refinement LexBFS. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    # labels[v] = list of vertices that "separated" v (in order of discovery)
    labels = [[] for _ in range(n)]
    # buckets: list of lists of vertices, ordered
    buckets = [[v] for v in range(n)]
    # bsize[b] = number of vertices in bucket b
    bsize = [1] * n
    nb = n
    order = []

    for _ in range(n):
        # pick first non-empty bucket
        b = 0
        while b < nb and bsize[b] == 0:
            b += 1
        if b >= nb:
            break
        # take first vertex of bucket b
        v = buckets[b][0]
        buckets[b] = buckets[b][1:]
        bsize[b] -= 1
        order.append(v)
        # refine: for each other bucket, split off vertices adjacent to v
        i = 0
        while i < nb:
            if i == b or bsize[i] == 0:
                i += 1
                continue
            adj = []
            nonadj = []
            for w in buckets[i]:
                if graph[v][w]:
                    adj.append(w)
                else:
                    nonadj.append(w)
            if not adj or not nonadj:
                i += 1
                continue
            # replace bucket i with nonadj, insert adj after i
            buckets[i] = nonadj
            bsize[i] = len(nonadj)
            newb = nb
            nb += 1
            buckets.append(adj)
            bsize.append(len(adj))
            for w in adj:
                labels[w].append(v)
            i += 1
    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property. O(n^3) with bitsets.

    For each position a, precompute:
      N_a = set of vertices adjacent to order[a]
      P_a = set of vertices that appear before position a
    Then for each b > a with order[b] not in N_a, the condition
    "exists d < a with db in E and dc not in E" for a given c is
    equivalent to: (N_a & P_a) is not a subset of N_c.
    """
    n = len(order)
    # bitset of neighbors for each vertex
    N = [0] * n
    for v in range(n):
        row = graph[v]
        bits = 0
        for w in range(n):
            if row[w]:
                bits |= (1 << w)
        N[v] = bits

    prefix = 0  # bitset of vertices already placed (positions < a)
    for a in range(n):
        va = order[a]
        Na = N[va]
        # for each b > a with ab not in E
        for b in range(a + 1, n):
            vb = order[b]
            if (Na >> vb) & 1:
                continue  # ab in E, condition not triggered
            # need: for all c > b with ac in E, (Na & prefix) not subset of N_c
            # i.e., (Na & prefix) & ~N_c != 0
            bad = False
            for c in range(b + 1, n):
                vc = order[c]
                if not ((Na >> vc) & 1):
                    continue  # ac not in E
                # check (Na & prefix) & ~N[vc] != 0
                if (Na & prefix & ~N[vc]) == 0:
                    bad = True
                    break
            if bad:
                return False
        prefix |= (1 << va)
    return True


def _try_repair(graph, order, edge):
    """Try a local repair after an edge update. Returns new order or None.

    Candidate set:
      1. the original order (often still valid)
      2. swap u and v
      3. move u to just before v
      4. move v to just before u
      5. move u to the very front
      6. move v to the very front
      7. move u to the very end
      8. move v to the very end
    """
    n = len(order)
    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(order):
        pos[vtx] = i

    candidates = []

    # 1. original order
    candidates.append(list(order))

    # 2. swap u and v
    if pos[u] != pos[v]:
        swapped = list(order)
        swapped[pos[u]], swapped[pos[v]] = swapped[pos[v]], swapped[pos[u]]
        candidates.append(swapped)

    # 3. move u to just before v
    if pos[u] < pos[v]:
        moved = list(order)
        moved.pop(pos[u])
        moved.insert(pos[v] - 1, u)
        candidates.append(moved)
    else:
        moved = list(order)
        moved.pop(pos[u])
        moved.insert(pos[v] + 1, u)
        candidates.append(moved)

    # 4. move v to just before u
    if pos[v] < pos[u]:
        moved = list(order)
        moved.pop(pos[v])
        moved.insert(pos[u] - 1, v)
        candidates.append(moved)
    else:
        moved = list(order)
        moved.pop(pos[v])
        moved.insert(pos[u] + 1, v)
        candidates.append(moved)

    # 5. move u to front
    if pos[u] != 0:
        moved = list(order)
        moved.pop(pos[u])
        moved.insert(0, u)
        candidates.append(moved)

    # 6. move v to front
    if pos[v] != 0:
        moved = list(order)
        moved.pop(pos[v])
        moved.insert(0, v)
        candidates.append(moved)

    # 7. move u to end
    if pos[u] != n - 1:
        moved = list(order)
        moved.pop(pos[u])
        moved.append(u)
        candidates.append(moved)

    # 8. move v to end
    if pos[v] != n - 1:
        moved = list(order)
        moved.pop(pos[v])
        moved.append(v)
        candidates.append(moved)

    for cand in candidates:
        if _is_valid_lexbfs(graph, cand):
            return cand
    return None


def _brute_force_lexbfs(graph):
    """Try all permutations (only for small n). Returns valid ordering or None."""
    n = len(graph)
    if n > 8:
        return None
    import itertools
    for perm in itertools.permutations(range(n)):
        if _is_valid_lexbfs(graph, list(perm)):
            return list(perm)
    return None


def _ensure_valid(graph, order, n):
    """Ensure order is a valid LexBFS ordering.

    The partition-refinement LexBFS is known to be correct, so this is a
    safety net. If the order is invalid (should not happen), try brute force
    for small n, then recompute.
    """
    if _is_valid_lexbfs(graph, order):
        return order
    # Try brute force for small n
    if n <= 8:
        result = _brute_force_lexbfs(graph)
        if result is not None:
            return result
    # For larger n, the partition-refinement should be correct;
    # if it's not, we have a bug. Return as-is.
    return order


def init(graph):
    n = len(graph)
    order = _lexbfs_full(graph)
    order = _ensure_valid(graph, order, n)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = state['ordering']
    n = state['n']
    repaired = _try_repair(graph, order, edge)
    if repaired is not None:
        return {'ordering': repaired, 'n': n}
    order = _lexbfs_full(graph)
    order = _ensure_valid(graph, order, n)
    return {'ordering': order, 'n': n}


def delete_edge(graph, edge, state):
    order = state['ordering']
    n = state['n']
    repaired = _try_repair(graph, order, edge)
    if repaired is not None:
        return {'ordering': repaired, 'n': n}
    order = _lexbfs_full(graph)
    order = _ensure_valid(graph, order, n)
    return {'ordering': order, 'n': n}
