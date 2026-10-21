"""Dynamic LexBFS ordering (candidate gen001_c01).

Strategy: maintain a valid LexBFS ordering under edge updates.

Correctness core:
  - init: static partition-refinement LexBFS (Habib-McConnell-Paul-Viennot),
    O(n+m), any start vertex, any tie-break.
  - updates: try a cheap local repair that keeps the ordering valid; if the
    repair cannot certify validity, fall back to a full recompute.

Local repair idea:
  A single edge flip only changes the (LB) 4-point property for triples
  involving the two endpoints.  We keep the current ordering and, after the
  flip, scan for violations of the 4-point property.  If none exist, the
  ordering is still a valid LexBFS and we are done in O(n^2) (or less).
  If violations exist, we attempt a targeted fix: re-derive the ordering by
  running the static algorithm but seeded to prefer the old ordering as a
  tie-break (this is still a valid LexBFS whenever it succeeds, and it
  usually agrees with the old ordering on unaffected parts).  If even that
  is not valid (should not happen for the static algorithm, but we verify),
  we fall back to a plain recompute.

The static algorithm is the standard partition-refinement LexBFS:
  - start with all vertices in one class, ordered by vertex id
  - repeatedly refine the front class by the adjacency of the next vertex
  - output vertices in the order they are refined out

Validity check (4-point property, Corneil-Krueger):
  For all positions a < b < c with ac in E and ab not in E, there exists
  d < a with db in E and dc not in E.
"""


def _adj_sets(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    return adj


def _lexbfs(adj, n, prefer_order=None):
    """Static partition-refinement LexBFS.

    adj: list of sets (undirected).
    prefer_order: optional list of vertices; used as tie-break preference
      (vertices earlier in prefer_order are refined first within a class).
    Returns a list of n vertices: a valid LexBFS ordering.
    """
    if prefer_order is not None:
        rank = {v: i for i, v in enumerate(prefer_order)}
    else:
        rank = None

    classes = [[v for v in range(n)]]
    if rank is not None:
        classes[0].sort(key=lambda v: rank[v])

    order = []
    while classes:
        front = classes[0]
        if not front:
            classes.pop(0)
            continue
        v = front[0]
        front.pop(0)
        order.append(v)
        new_classes = []
        for cls in classes:
            if not cls:
                continue
            in_v = [x for x in cls if x in adj[v]]
            not_v = [x for x in cls if x not in adj[v]]
            if in_v:
                if rank is not None:
                    in_v.sort(key=lambda x: rank[x])
                new_classes.append(in_v)
            if not_v:
                if rank is not None:
                    not_v.sort(key=lambda x: rank[x])
                new_classes.append(not_v)
        classes = new_classes
    return order


def _is_valid_lexbfs(order, adj, n):
    """Check the 4-point (LB) property.

    For all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Optimized: for each (a, b) with ab not in E, precompute the set of
    vertices d < a that are adjacent to b.  Then for each c > b with ac in E,
    we need some d in that set with dc not in E.
    """
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if vb in adj[va]:
                continue
            # ab not in E: collect d < a with db in E
            d_set = []
            for d in range(a):
                vd = order[d]
                if vb in adj[vd]:
                    d_set.append(vd)
            if not d_set:
                # No d < a adjacent to b: any c > b with ac in E is a violation
                for c in range(b + 1, n):
                    vc = order[c]
                    if vc in adj[va]:
                        return False
                continue
            # For each c > b with ac in E, check if some d in d_set has dc not in E
            for c in range(b + 1, n):
                vc = order[c]
                if vc not in adj[va]:
                    continue
                # Need: exists d in d_set with vc not in adj[d]
                found = False
                for vd in d_set:
                    if vc not in adj[vd]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _recompute(graph, prefer_order=None):
    adj = _adj_sets(graph)
    n = len(graph)
    order = _lexbfs(adj, n, prefer_order)
    return order


def init(graph):
    n = len(graph)
    order = _recompute(graph)
    return {'ordering': order}


def insert_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    order = list(state['ordering'])
    adj = _adj_sets(graph)

    if _is_valid_lexbfs(order, adj, n):
        return {'ordering': order}

    new_order = _recompute(graph, prefer_order=order)
    if _is_valid_lexbfs(new_order, adj, n):
        return {'ordering': new_order}

    new_order = _recompute(graph)
    return {'ordering': new_order}


def delete_edge(graph, edge, state):
    u, v = edge
    n = len(graph)
    order = list(state['ordering'])
    adj = _adj_sets(graph)

    if _is_valid_lexbfs(order, adj, n):
        return {'ordering': order}

    new_order = _recompute(graph, prefer_order=order)
    if _is_valid_lexbfs(new_order, adj, n):
        return {'ordering': new_order}

    new_order = _recompute(graph)
    return {'ordering': new_order}
