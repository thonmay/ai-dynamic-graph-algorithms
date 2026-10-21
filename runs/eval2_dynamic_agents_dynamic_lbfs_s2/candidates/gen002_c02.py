"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try a cheap
local repair (move one of the affected vertices to a different position).
If the local repair fails, fall back to a full static LexBFS recomputation.
The state caches adjacency sets for fast lookups.
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


def _lexbfs(adj):
    """Static LexBFS via label-based selection.

    Returns a list of vertices in LexBFS order.
    """
    n = len(adj)
    if n == 0:
        return []

    order = []
    remaining = list(range(n))
    processed = [-1] * n

    while remaining:
        best = None
        best_label = None
        for v in remaining:
            label = []
            for u in adj[v]:
                if processed[u] >= 0:
                    label.append(processed[u])
            label.sort()
            if best_label is None or label < best_label:
                best_label = label
                best = v
        remaining.remove(best)
        processed[best] = len(order)
        order.append(best)

    return order


def _is_valid_lexbfs(order, adj):
    """Check the (LB) 4-point property.

    For all positions a < c < b with ab in E and ac not in E,
    there exists d < a with db in E and dc not in E.
    """
    n = len(order)
    for a in range(n):
        va = order[a]
        for c in range(a + 1, n):
            vc = order[c]
            if va in adj[vc]:
                continue  # ac in E, skip
            for b in range(c + 1, n):
                vb = order[b]
                if va not in adj[vb]:
                    continue  # ab not in E, skip
                found = False
                for d in range(a):
                    vd = order[d]
                    if vb in adj[vd] and vc not in adj[vd]:
                        found = True
                        break
                if not found:
                    return False
    return True


def _local_repair(order, adj, vertex):
    """Try to repair the ordering by moving `vertex` to a different position.

    Returns a new ordering if valid, else None.
    """
    n = len(order)
    if n == 0:
        return order
    if vertex not in adj:
        return None

    cur_pos = order.index(vertex)

    # Remove vertex from order
    base = [v for i, v in enumerate(order) if i != cur_pos]

    # Try inserting at each position, starting near cur_pos and expanding
    # outward.  This way we find a valid position quickly if one exists
    # nearby.
    for d in range(n):
        for insert_pos in (cur_pos + d, cur_pos - d):
            if insert_pos < 0 or insert_pos >= n:
                continue
            candidate = base[:insert_pos] + [vertex] + base[insert_pos:]
            if _is_valid_lexbfs(candidate, adj):
                return candidate
    return None


def init(graph):
    adj = _adj_sets(graph)
    order = _lexbfs(adj)
    return {'ordering': order, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].add(v)
    adj[v].add(u)

    order = state['ordering']

    # Try local repair: move u or v to a better position
    new_order = _local_repair(order, adj, u)
    if new_order is None:
        new_order = _local_repair(order, adj, v)
    if new_order is None:
        new_order = _lexbfs(adj)

    return {'ordering': new_order, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].discard(v)
    adj[v].discard(u)

    order = state['ordering']

    new_order = _local_repair(order, adj, u)
    if new_order is None:
        new_order = _local_repair(order, adj, v)
    if new_order is None:
        new_order = _lexbfs(adj)

    return {'ordering': new_order, 'adj': adj}
