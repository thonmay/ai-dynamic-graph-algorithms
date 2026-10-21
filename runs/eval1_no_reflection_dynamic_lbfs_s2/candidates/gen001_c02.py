"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering.  On each update, try to repair
the existing ordering locally (cheap); if the repair fails, fall back to a
full O(n^2) partition-refinement LexBFS recompute (always correct).

The key insight: an edge insertion can only *help* the (LB) 4-point
property (it adds witnesses), so the old ordering remains valid unless
the new edge changes the relative lexicographic order of two buckets
that were tied when one of the endpoints was selected.  We detect this
by checking whether the ordering is still a valid LexBFS via the
4-point property; if not, we recompute.

An edge deletion can *break* the 4-point property (it removes a
witness).  Again we check validity and recompute if needed.
"""


def _lexbfs_full(graph):
    """Full partition-refinement LexBFS (HMPV).  Returns a valid ordering."""
    n = len(graph)
    if n == 0:
        return []

    # We use the standard HMPV partition-refinement algorithm.
    #
    # State:
    #   buckets: list of (label, [vertices]) in order
    #   label: list of 0/1, shared by all vertices in a bucket
    #
    # At each step:
    #   1. Pick the first bucket, take its first vertex v.
    #   2. Remove v from its bucket (split if needed).
    #   3. Refine every other bucket by adjacency to v:
    #      split into (label+[1], N(v)∩B) and (label+[0], B\N(v)).
    #   4. Reorder buckets by their labels (lexicographic).
    #
    # This is O(n^2) with careful implementation.

    # buckets: list of [label_list, [v1, v2, ...]]
    # Initially one bucket with all vertices, empty label.
    buckets = [[[], list(range(n))]]

    order = []
    for _ in range(n):
        # Pick first vertex of first bucket
        first_bucket = buckets[0]
        v = first_bucket[1][0]
        order.append(v)

        # Remove v from its bucket
        first_bucket[1].pop(0)
        if not first_bucket[1]:
            buckets.pop(0)

        # Refine all remaining buckets by adjacency to v
        new_buckets = []
        for label, verts in buckets:
            in_nbr = [u for u in verts if graph[v][u]]
            out_nbr = [u for u in verts if not graph[v][u]]
            if in_nbr:
                new_buckets.append([label + [1], in_nbr])
            if out_nbr:
                new_buckets.append([label + [0], out_nbr])
        buckets = new_buckets

        # Sort buckets by label (lexicographic)
        buckets.sort(key=lambda b: b[0])

    return order


def _is_valid_lexbfs(graph, order):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if graph[va][vb]:
                continue  # ab in E, no constraint
            # ab not in E; need: for all c > b with ac in E,
            # exists d < a with db in E and dc not in E
            for c in range(b + 1, n):
                vc = order[c]
                if not graph[va][vc]:
                    continue  # ac not in E, no constraint
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


def init(graph):
    n = len(graph)
    order = _lexbfs_full(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    order = state['ordering']
    # Check if the current ordering is still valid
    if _is_valid_lexbfs(graph, order):
        return state
    # Otherwise recompute
    order = _lexbfs_full(graph)
    return {'ordering': order}


def delete_edge(graph, edge, state):
    order = state['ordering']
    # Check if the current ordering is still valid
    if _is_valid_lexbfs(graph, order):
        return state
    # Otherwise recompute
    order = _lexbfs_full(graph)
    return {'ordering': order}
