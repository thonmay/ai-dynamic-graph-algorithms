"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering. On each update, try a cheap
local repair (re-run LexBFS on a suffix of the ordering); if the repair
cannot certify validity, fall back to a full O(n^3) LexBFS recompute.

The local repair is correct: if we fix the prefix of the ordering up to
position k-1 and re-run the greedy LexBFS process on the remaining
vertices (with labels initialized from adjacency to the prefix), the
result is a valid LexBFS for the whole graph. This is because LexBFS is
a greedy process: once a vertex is output, its label is frozen, and the
choice among remaining vertices depends only on their current labels.

The key insight for efficiency: after an edge update (u,v), only labels
at positions >= min(pos[u], pos[v]) can change. So we can fix the prefix
up to min(pos[u], pos[v]) - 1 and re-run on the suffix. This is O(k^2)
for suffix length k, much less than O(n^2) when the update is local.
"""


def _lexbfs_full(graph):
    """Full LexBFS. Returns ordering list."""
    n = len(graph)
    remaining = list(range(n))
    ordering = []
    labels = [tuple(0 for _ in range(n)) for _ in range(n)]
    while remaining:
        best = None
        best_label = None
        for v in remaining:
            if best is None or labels[v] < best_label or (labels[v] == best_label and v < best):
                best = v
                best_label = labels[v]
        ordering.append(best)
        remaining.remove(best)
        pos = len(ordering) - 1
        for v in remaining:
            lbl = list(labels[v])
            lbl[pos] = graph[v][best]
            labels[v] = tuple(lbl)
    return ordering


def _verify_lexbfs(graph, ordering):
    """Check the (LB) 4-point property. Returns True if valid."""
    n = len(graph)
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                if graph[ordering[a]][ordering[c]] and not graph[ordering[a]][ordering[b]]:
                    found = False
                    for d in range(a):
                        if graph[ordering[d]][ordering[b]] and not graph[ordering[d]][ordering[c]]:
                            found = True
                            break
                    if not found:
                        return False
    return True


def _lexbfs_suffix(graph, prefix, suffix):
    """Run LexBFS on the suffix vertices, given the prefix is already fixed.
    
    prefix: list of vertices already ordered (in order).
    suffix: list of vertices to order.
    Returns the full ordering (prefix + new suffix ordering).
    """
    n = len(graph)
    p = len(prefix)
    labels = {}
    for v in suffix:
        lbl = [0] * n
        for i, u in enumerate(prefix):
            lbl[i] = graph[v][u]
        labels[v] = tuple(lbl)
    remaining = list(suffix)
    ordering = list(prefix)
    while remaining:
        best = None
        best_label = None
        for v in remaining:
            if best is None or labels[v] < best_label or (labels[v] == best_label and v < best):
                best = v
                best_label = labels[v]
        ordering.append(best)
        remaining.remove(best)
        pos = len(ordering) - 1
        for v in remaining:
            lbl = list(labels[v])
            lbl[pos] = graph[v][best]
            labels[v] = tuple(lbl)
    return ordering


def init(graph):
    n = len(graph)
    ordering = _lexbfs_full(graph)
    return {'ordering': ordering, 'n': n}


def _try_local_repair(graph, state, u, v):
    """Try to repair the ordering locally after an edge update.
    
    Returns a new ordering if the repair is valid, else None.
    """
    ordering = state['ordering']
    n = state['n']
    pos = [0] * n
    for i, w in enumerate(ordering):
        pos[w] = i
    pu, pv = pos[u], pos[v]
    start = min(pu, pv)
    prefix = ordering[:start]
    suffix = ordering[start:]
    new_ordering = _lexbfs_suffix(graph, prefix, suffix)
    if _verify_lexbfs(graph, new_ordering):
        return new_ordering
    return None


def insert_edge(graph, edge, state):
    u, v = edge
    new_ordering = _try_local_repair(graph, state, u, v)
    if new_ordering is not None:
        state['ordering'] = new_ordering
        return state
    state['ordering'] = _lexbfs_full(graph)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    new_ordering = _try_local_repair(graph, state, u, v)
    if new_ordering is not None:
        state['ordering'] = new_ordering
        return state
    state['ordering'] = _lexbfs_full(graph)
    return state
