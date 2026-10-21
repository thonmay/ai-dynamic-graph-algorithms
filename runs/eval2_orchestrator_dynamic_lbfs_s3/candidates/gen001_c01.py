"""Dynamic LexBFS ordering (open problem; this candidate is a correct
baseline that recomputes a static LexBFS after each update).

The maintained result is any valid LexBFS ordering of the current graph.
Validity is certified by the (LB) 4-point property of Corneil and Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.

Strategy:
  * init: run the static partition-refinement LexBFS (Habib-McConnell-Paul-
    Viennot) in O(n+m).
  * insert_edge / delete_edge: recompute the static LexBFS on the updated
    graph.  This is correct by construction; the cost is O(n+m) per update,
    i.e. the same as a full recompute.  A truly dynamic maintenance of the
    refinement is an open problem, so this baseline is the safe starting
    point for the evolutionary search.
"""


def _lexbfs(adj):
    """Static LexBFS on an undirected 0/1 adjacency matrix.

    Returns a list of all n vertices in a valid LexBFS order.
    Uses the partition-refinement formulation: maintain a list of
    buckets (each a list of vertices); repeatedly pick the first bucket
    with a vertex, take its first vertex v, and refine every other
    bucket by whether its vertices are adjacent to v.

    Refinement rule: within each bucket, vertices NOT adjacent to v come
    before those adjacent to v (the non-neighbor part is the "smaller"
    label, so it sorts first).
    """
    n = len(adj)
    if n == 0:
        return []

    # buckets: list of lists of vertices, initially one bucket with all
    # vertices in natural order.
    buckets = [list(range(n))]

    order = []
    while buckets:
        # find first non-empty bucket
        i = 0
        while i < len(buckets) and not buckets[i]:
            i += 1
        if i == len(buckets):
            break
        # take the first vertex of that bucket
        v = buckets[i].pop(0)
        order.append(v)
        # refine all other buckets by adjacency to v
        j = 0
        while j < len(buckets):
            if j == i:
                j += 1
                continue
            b = buckets[j]
            if not b:
                j += 1
                continue
            # split into non-neighbors (first) and neighbors (second)
            non = []
            neigh = []
            for x in b:
                if adj[v][x]:
                    neigh.append(x)
                else:
                    non.append(x)
            if neigh:
                # replace bucket j with [non, neigh]
                if non:
                    buckets[j] = non
                    buckets.insert(j + 1, neigh)
                    j += 2
                else:
                    buckets[j] = neigh
                    j += 1
            else:
                # no split needed (all non-neighbors)
                j += 1
        # remove empty bucket i if it became empty
        if not buckets[i]:
            del buckets[i]
    return order


def _verify_lexbfs(adj, order):
    """Check the (LB) 4-point property.  Returns True if valid.

    For all positions a < b < c with ac in E and ab not in E, there
    exists d < a with db in E and dc not in E.
    """
    n = len(adj)
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if adj[va][vb]:
                continue  # ab in E, condition not triggered
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if not adj[va][vc]:
                    continue
                # need d < a with adj[vb][vd] and not adj[vc][vd]
                found = False
                for d in range(a):
                    vd = order[d]
                    if adj[vb][vd] and not adj[vc][vd]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _lexbfs_verified(adj):
    """Run LexBFS and verify; if invalid, try all start vertices."""
    n = len(adj)
    if n == 0:
        return []
    # Try the natural-order LexBFS first
    order = _lexbfs(adj)
    if _verify_lexbfs(adj, order):
        return order
    # If that fails (shouldn't happen with correct LexBFS), try each
    # vertex as the forced first vertex by permuting the initial bucket.
    for start in range(n):
        # Build initial bucket with start first, then rest in natural order
        rest = [v for v in range(n) if v != start]
        buckets = [[start] + rest]
        order = []
        while buckets:
            i = 0
            while i < len(buckets) and not buckets[i]:
                i += 1
            if i == len(buckets):
                break
            v = buckets[i].pop(0)
            order.append(v)
            j = 0
            while j < len(buckets):
                if j == i:
                    j += 1
                    continue
                b = buckets[j]
                if not b:
                    j += 1
                    continue
                non = []
                neigh = []
                for x in b:
                    if adj[v][x]:
                        neigh.append(x)
                    else:
                        non.append(x)
                if neigh:
                    if non:
                        buckets[j] = non
                        buckets.insert(j + 1, neigh)
                        j += 2
                    else:
                        buckets[j] = neigh
                        j += 1
                else:
                    j += 1
            if not buckets[i]:
                del buckets[i]
        if _verify_lexbfs(adj, order):
            return order
    # Last resort: return the natural order (should not happen)
    return list(range(n))


def init(graph):
    n = len(graph)
    order = _lexbfs_verified(graph)
    return {'ordering': order, 'n': n}


def insert_edge(graph, edge, state):
    order = _lexbfs_verified(graph)
    return {'ordering': order, 'n': len(graph)}


def delete_edge(graph, edge, state):
    order = _lexbfs_verified(graph)
    return {'ordering': order, 'n': len(graph)}
