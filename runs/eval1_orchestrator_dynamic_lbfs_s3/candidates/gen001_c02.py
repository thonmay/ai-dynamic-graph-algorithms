"""Dynamic LexBFS ordering.

Maintains a valid LexBFS ordering under edge insertions and deletions.
After an update, tries a local repair (a few candidate re-orderings checked
against the (LB) 4-point property); falls back to a full O(n^2) LexBFS
recompute if the local repair fails.

The (LB) 4-point property (Corneil & Krueger): an ordering is a valid
LexBFS ordering iff for all positions i < j < k,
  if ordering[k] ~ ordering[i] and ordering[k] !~ ordering[j],
  then exists h < i with ordering[h] ~ ordering[j] and ordering[h] !~ ordering[k].

Equivalent subset formulation used for verification:
  For all positions j < k:
    N(ordering[k]) ∩ [0, j) ⊆ N(ordering[j]) ∩ [0, j)
  where [0, j) = {ordering[i] : i < j}.
"""


def _build_adj(graph):
    """Build adjacency bitsets from a 0/1 adjacency matrix."""
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


def _lexbfs_ordering(graph):
    """Compute a LexBFS ordering from scratch (partition refinement)."""
    n = len(graph)
    if n == 0:
        return []

    adj = _build_adj(graph)

    # Buckets: list of lists of vertex ids.
    buckets = [list(range(n))]
    order = []

    for _ in range(n):
        v = buckets[0][0]
        order.append(v)
        buckets[0].pop(0)
        if not buckets[0]:
            buckets.pop(0)

        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            nbrs = []
            non_nbrs = []
            for x in bucket:
                if (adj[v] >> x) & 1:
                    nbrs.append(x)
                else:
                    non_nbrs.append(x)
            if nbrs:
                new_buckets.append(nbrs)
            if non_nbrs:
                new_buckets.append(non_nbrs)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property via the subset formulation.

    For all positions j < k:
      N(ordering[k]) ∩ [0, j) ⊆ N(ordering[j]) ∩ [0, j)
    i.e. for all i < j: if ordering[i] ~ ordering[k] then ordering[i] ~ ordering[j].
    """
    n = len(ordering)
    if n <= 2:
        return True

    adj = _build_adj(graph)

    for j in range(n):
        vj = ordering[j]
        adj_j = adj[vj]
        for k in range(j + 1, n):
            vk = ordering[k]
            adj_k = adj[vk]
            for i in range(j):
                vi = ordering[i]
                if (adj_k >> vi) & 1:
                    if not ((adj_j >> vi) & 1):
                        return False
    return True


def _try_local_fix(graph, ordering, edge, is_insert):
    """Try to repair the ordering locally.  Returns a new ordering or None."""
    n = len(ordering)
    u, v = edge
    pos = [0] * n
    for i, x in enumerate(ordering):
        pos[x] = i

    if is_insert:
        # Try moving the later of u,v to just before the earlier.
        if pos[u] > pos[v]:
            earlier, later = v, u
        else:
            earlier, later = u, v
        new_ordering = list(ordering)
        new_ordering.remove(later)
        idx = new_ordering.index(earlier)
        new_ordering.insert(idx, later)
        if _is_valid_lexbfs(graph, new_ordering):
            return new_ordering

        # Try moving the earlier of u,v to just after the later.
        new_ordering2 = list(ordering)
        new_ordering2.remove(earlier)
        idx2 = new_ordering2.index(later)
        new_ordering2.insert(idx2 + 1, earlier)
        if _is_valid_lexbfs(graph, new_ordering2):
            return new_ordering2

        return None
    else:
        # Deletion: first check if the original ordering is still valid.
        if _is_valid_lexbfs(graph, ordering):
            return ordering

        # Try swapping u and v (if adjacent in the ordering).
        if abs(pos[u] - pos[v]) == 1:
            new_ordering = list(ordering)
            new_ordering[pos[u]], new_ordering[pos[v]] = new_ordering[pos[v]], new_ordering[pos[u]]
            if _is_valid_lexbfs(graph, new_ordering):
                return new_ordering

        # Try moving the later of u,v to just before the earlier.
        if pos[u] > pos[v]:
            earlier, later = v, u
        else:
            earlier, later = u, v
        new_ordering = list(ordering)
        new_ordering.remove(later)
        idx = new_ordering.index(earlier)
        new_ordering.insert(idx, later)
        if _is_valid_lexbfs(graph, new_ordering):
            return new_ordering

        return None


def init(graph):
    n = len(graph)
    ordering = _lexbfs_ordering(graph)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    fixed = _try_local_fix(graph, ordering, edge, is_insert=True)
    if fixed is not None:
        state['ordering'] = fixed
        return state
    state['ordering'] = _lexbfs_ordering(graph)
    return state


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    fixed = _try_local_fix(graph, ordering, edge, is_insert=False)
    if fixed is not None:
        state['ordering'] = fixed
        return state
    state['ordering'] = _lexbfs_ordering(graph)
    return state
