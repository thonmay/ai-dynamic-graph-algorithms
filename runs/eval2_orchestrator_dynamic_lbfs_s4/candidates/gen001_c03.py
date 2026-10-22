"""Dynamic LexBFS ordering (candidate gen001_c03).

Strategy:
- init: static partition-refinement LexBFS (HMPV), deterministic tie-break.
- insert_edge / delete_edge: verify the existing ordering against the
  (LB) 4-point property of Corneil & Krueger using bitmasks; if still
  valid, keep it (no recompute).  Otherwise recompute from scratch.

Correctness: the 4-point property is a necessary and sufficient condition
for an ordering to be a LexBFS ordering, so verification is exact.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement.  Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # buckets: list of sets, forming a partition of remaining vertices
    buckets = [set(range(n))]
    order = []

    for _ in range(n):
        # Pick smallest vertex from first non-empty bucket
        v = None
        for B in buckets:
            if B:
                v = min(B)
                break
        if v is None:
            break
        order.append(v)

        # Remove v from its bucket
        for B in buckets:
            if v in B:
                B.discard(v)
                break

        # Refine: split each bucket by adjacency to v
        new_buckets = []
        for B in buckets:
            if not B:
                continue
            B1 = set()
            B2 = set()
            for u in B:
                if graph[u][v]:
                    B1.add(u)
                else:
                    B2.add(u)
            if B1:
                new_buckets.append(B1)
            if B2:
                new_buckets.append(B2)
        buckets = new_buckets

    return order


def _is_valid_lexbfs(graph, ordering):
    """Check (LB) 4-point property: for all positions a < b < c with
    ac in E and ab not in E, exists d < a with db in E and dc not in E.

    Uses bitmasks for O(n^3 / word_size) verification.
    """
    n = len(graph)
    # adj_mask[v] = bitmask of neighbors of v
    adj_mask = [0] * n
    for i in range(n):
        row = graph[i]
        mask = 0
        for j in range(n):
            if row[j]:
                mask |= (1 << j)
        adj_mask[i] = mask

    # prefix_mask[k] = bitmask of vertices at positions 0..k-1
    prefix_mask = [0] * (n + 1)
    for i in range(n):
        prefix_mask[i + 1] = prefix_mask[i] | (1 << ordering[i])

    for c in range(n):
        vc = ordering[c]
        adj_vc = adj_mask[vc]
        for a in range(c):
            va = ordering[a]
            if not (adj_vc >> va) & 1:
                continue  # ac not in E
            # S = {d < a : dc not in E}
            S = prefix_mask[a] & ~adj_vc
            if S == 0:
                # No witness possible; any b with ab not in E fails
                adj_va = adj_mask[va]
                for b in range(a + 1, c):
                    vb = ordering[b]
                    if not (adj_va >> vb) & 1:
                        return False
                continue
            adj_va = adj_mask[va]
            for b in range(a + 1, c):
                vb = ordering[b]
                if (adj_va >> vb) & 1:
                    continue  # ab in E, no constraint
                # Need some d in S with db in E
                if (adj_mask[vb] & S) == 0:
                    return False
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    ordering = state['ordering']
    if _is_valid_lexbfs(graph, ordering):
        return state
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
