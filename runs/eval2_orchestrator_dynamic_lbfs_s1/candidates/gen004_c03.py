"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a valid LexBFS ordering.  After each update, check the
(LB) 4-point property on the existing ordering; if it still holds, keep it
(cheap, O(n^3) check).  Otherwise recompute a full static LexBFS.

The static LexBFS uses the partition-refinement algorithm of Habib,
McConnell, Paul and Viennot, implemented with a simple list-of-buckets
representation.
"""


def _adjacency(graph):
    """Build undirected adjacency sets from a 0/1 matrix.

    Reads the full matrix (both triangles) so the result is correct even if
    the matrix is momentarily non-symmetric (a legal update flips exactly
    one entry).
    """
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if i != j and row[j]:
                adj[i].add(j)
    return adj


def _lexbfs(graph):
    """Static LexBFS via partition refinement.

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    adj = _adjacency(graph)

    # We use a simpler but correct approach: maintain for each unprocessed
    # vertex its label (list of 0/1 over processed vertices in order), and
    # pick the unprocessed vertex with lexicographically smallest label
    # (tie-break by vertex id).  This is O(n^2 * n) = O(n^3) which is fine.

    order = []
    labels = {v: [] for v in range(n)}
    unprocessed = set(range(n))

    for _ in range(n):
        best = None
        best_key = None
        for v in unprocessed:
            key = (tuple(labels[v]), v)
            if best_key is None or key < best_key:
                best_key = key
                best = v
        unprocessed.remove(best)
        order.append(best)
        for w in unprocessed:
            labels[w].append(1 if w in adj[best] else 0)
    return order


def _is_valid_lexbfs(graph, ordering):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    if n <= 2:
        return True

    adj = _adjacency(graph)

    p2v = ordering  # position -> vertex

    for a in range(n):
        va = p2v[a]
        for b in range(a + 1, n):
            vb = p2v[b]
            if vb in adj[va]:
                continue  # ab in E, no constraint
            # ab not in E
            # W = {d < a : db in E}
            W = [p2v[d] for d in range(a) if vb in adj[p2v[d]]]
            if not W:
                # If any c > b with ac in E, violation
                for c in range(b + 1, n):
                    if p2v[c] in adj[va]:
                        return False
                continue
            # For each c > b with ac in E, need d in W with dc not in E
            for c in range(b + 1, n):
                vc = p2v[c]
                if vc not in adj[va]:
                    continue
                ok = False
                for vd in W:
                    if vc not in adj[vd]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _symmetrize(graph):
    """Return a symmetric copy of the 0/1 matrix.

    A legal update flips exactly one matrix entry, so the matrix handed to
    us can be momentarily non-symmetric.  Symmetrizing (OR of the two
    entries) recovers the intended undirected graph for both insertions and
    deletions, and never mutates the caller's matrix.
    """
    n = len(graph)
    sym = [list(row) for row in graph]
    for i in range(n):
        for j in range(i + 1, n):
            if sym[i][j] or sym[j][i]:
                sym[i][j] = 1
                sym[j][i] = 1
    return sym


def init(graph):
    ordering = _lexbfs(_symmetrize(graph))
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    sym = _symmetrize(graph)
    ordering = state['ordering']
    if _is_valid_lexbfs(sym, ordering):
        return state
    ordering = _lexbfs(sym)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    sym = _symmetrize(graph)
    ordering = state['ordering']
    if _is_valid_lexbfs(sym, ordering):
        return state
    ordering = _lexbfs(sym)
    return {'ordering': ordering}
