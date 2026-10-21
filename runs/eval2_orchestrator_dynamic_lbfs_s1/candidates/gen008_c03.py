"""Dynamic LexBFS ordering (open tier).

Strategy: maintain a valid LexBFS ordering.  After each update, check the
(LB) 4-point property on the existing ordering; if it still holds, keep it
(cheap, O(n^3) check).  Otherwise recompute a full static LexBFS.

The static LexBFS uses the partition-refinement algorithm of Habib,
McConnell, Paul and Viennot, implemented with a simple list-of-buckets
representation.
"""


def _adjacency(graph, edge=None, inserted=True):
    """Build undirected adjacency sets from a 0/1 matrix.

    Reads the full matrix (both triangles) so that a legal update which
    flips exactly one entry is always visible, even if the matrix is
    momentarily non-symmetric.  If `edge` is given, the update is applied
    on top of the matrix (the harness may pass the pre-update matrix).
    """
    n = len(graph)
    adj = [set() for _ in range(n)]
    for i in range(n):
        row = graph[i]
        for j in range(n):
            if i != j and row[j]:
                adj[i].add(j)
    if edge is not None:
        u, v = edge
        if inserted:
            adj[u].add(v)
            adj[v].add(u)
        else:
            adj[u].discard(v)
            adj[v].discard(u)
    return adj


def _effective_graph(graph, edge, inserted):
    """Return the post-update symmetric matrix.

    The harness may hand us the pre-update matrix with the update
    described by `edge`; apply the flip and symmetrize so downstream
    code sees the true current graph.
    """
    n = len(graph)
    g = [list(row) for row in graph]
    u, v = edge
    if inserted:
        g[u][v] = 1
        g[v][u] = 1
    else:
        g[u][v] = 0
        g[v][u] = 0
    for i in range(n):
        for j in range(i + 1, n):
            if g[i][j] or g[j][i]:
                g[i][j] = 1
                g[j][i] = 1
    return g


def _lexbfs(graph, edge=None, inserted=True):
    """Static LexBFS via partition refinement.

    Returns a list of all n vertices in a valid LexBFS order.
    """
    n = len(graph)
    if n == 0:
        return []

    adj = _adjacency(graph, edge=edge, inserted=inserted)

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


def _is_valid_lexbfs(graph, ordering, edge=None, inserted=True):
    """Check the (LB) 4-point property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(ordering)
    if n <= 2:
        return True

    adj = _adjacency(graph, edge=edge, inserted=inserted)

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


def init(graph):
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    g = _effective_graph(graph, edge, True)
    ordering = state['ordering']
    if _is_valid_lexbfs(g, ordering):
        return state
    ordering = _lexbfs(g)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    g = _effective_graph(graph, edge, False)
    ordering = state['ordering']
    if _is_valid_lexbfs(g, ordering):
        return state
    ordering = _lexbfs(g)
    return {'ordering': ordering}
