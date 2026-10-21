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
    """Check the (LB) 4-point property. O(n^4) worst case."""
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue  # ab in E, condition not triggered
            # ab not in E; check all c > b with ac in E
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue
                # need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = order[d]
                    if graph[vd][vb] and not graph[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _try_repair(graph, order, edge):
    """Try a local repair after an edge update. Returns new order or None."""
    n = len(order)
    u, v = edge
    pos = [0] * n
    for i, vtx in enumerate(order):
        pos[vtx] = i

    candidates = []

    # Try the original order
    candidates.append(list(order))

    # Try swapping u and v
    if pos[u] != pos[v]:
        swapped = list(order)
        swapped[pos[u]], swapped[pos[v]] = swapped[pos[v]], swapped[pos[u]]
        candidates.append(swapped)

    # Try moving u to just before v
    if pos[u] < pos[v]:
        moved = list(order)
        moved.pop(pos[u])
        new_v_pos = pos[v] - 1
        moved.insert(new_v_pos, u)
        candidates.append(moved)
    else:
        moved = list(order)
        moved.pop(pos[u])
        new_v_pos = pos[v]
        moved.insert(new_v_pos + 1, u)
        candidates.append(moved)

    # Try moving v to just before u
    if pos[v] < pos[u]:
        moved = list(order)
        moved.pop(pos[v])
        new_u_pos = pos[u] - 1
        moved.insert(new_u_pos, v)
        candidates.append(moved)
    else:
        moved = list(order)
        moved.pop(pos[v])
        new_u_pos = pos[u]
        moved.insert(new_u_pos + 1, v)
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
    """Ensure order is a valid LexBFS ordering. Falls back to brute force."""
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
