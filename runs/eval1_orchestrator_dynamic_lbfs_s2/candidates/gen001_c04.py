"""Dynamic LexBFS ordering (open tier).

Strategy:
- init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot), O(n+m).
- insert_edge(u,v): check if current ordering is still valid via the (LB)
  4-point property in O(n^2); if valid, keep it; else recompute.
- delete_edge(u,v): recompute from scratch (deletion can break validity).

The (LB) property (Corneil-Krueger): for all a < b < c in the ordering with
ac in E and ab not in E, there exists d < a with db in E and dc not in E.
It characterizes exactly the LexBFS orderings.
"""


def _lexbfs(adj, n):
    """Static partition-refinement LexBFS (HMPV). Returns an ordering list.

    Algorithm:
    - Maintain a list of buckets (each a list of vertices, in order).
    - Repeatedly: take the first non-empty bucket, take its first vertex x.
      Output x. Split the REMAINDER of that bucket by adjacency to x:
      neighbors of x come first, non-neighbors of x come second.
      Both new sub-buckets are inserted at the front of the bucket list.
    """
    buckets = [list(range(n))]

    order = []
    while True:
        # Find first non-empty bucket
        bi = -1
        for i in range(len(buckets)):
            if buckets[i]:
                bi = i
                break
        if bi == -1:
            break

        b = buckets[bi]
        x = b[0]
        order.append(x)

        # Remove x from its bucket
        b = b[1:]

        # Split the remainder of this bucket by adjacency to x
        adjb = []
        nonadj = []
        for y in b:
            if adj[x][y]:
                adjb.append(y)
            else:
                nonadj.append(y)

        # Replace bucket bi with: adjb (if non-empty), nonadj (if non-empty)
        new_parts = []
        if adjb:
            new_parts.append(adjb)
        if nonadj:
            new_parts.append(nonadj)
        buckets[bi:bi+1] = new_parts

    return order


def _is_valid_lexbfs(adj, n, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    for a in range(n):
        va = ordering[a]
        for b in range(a + 1, n):
            vb = ordering[b]
            if adj[va][vb]:
                continue  # ab in E, skip
            # ab not in E; check all c > b with ac in E
            for c in range(b + 1, n):
                vc = ordering[c]
                if not adj[va][vc]:
                    continue  # ac not in E, skip
                # Need d < a with db in E and dc not in E
                found = False
                for d in range(a):
                    vd = ordering[d]
                    if adj[vd][vb] and not adj[vd][vc]:
                        found = True
                        break
                if not found:
                    return False
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}


def insert_edge(graph, edge, state):
    n = state['n']
    ordering = state['ordering']
    # Check if the current ordering is still valid
    if _is_valid_lexbfs(graph, n, ordering):
        return state
    # Otherwise recompute
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}


def delete_edge(graph, edge, state):
    n = state['n']
    # Deletion can break validity; recompute
    ordering = _lexbfs(graph, n)
    return {'ordering': ordering, 'n': n}
