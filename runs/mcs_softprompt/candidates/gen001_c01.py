"""Dynamic MCS (undirected): maintain a valid maximal-cardinality-search
ordering under single-edge insertions and deletions.

Approach: keep the current ordering. A single edge flip can only break the
greedy (max-cardinality) property in a suffix, so we keep the still-valid
prefix and re-derive the remaining vertices with one fresh greedy pass.
  - insert (x,y) with x before y: the prefix through x stays valid,
    so recompute from position pos[x] + 1.
  - delete (x,y) with x before y: the prefix through y-1 stays valid,
    so recompute from position pos[y].
The maintained ordering always satisfies the MCS invariant: every vertex is
chosen while its cardinality (number of already-chosen neighbors) is maximal
among the not-yet-chosen vertices.
"""


def _mcs_suffix(graph, prefix, remaining):
    """Greedy MCS over `remaining` with `prefix` already fixed.

    Returns the order in which the remaining vertices are chosen. Each
    vertex's cardinality counts its neighbors in (prefix + already chosen).
    Ties are broken by lowest vertex id.
    """
    prefix_set = set(prefix)
    card = {v: 0 for v in remaining}
    for v in remaining:
        row = graph[v]
        for u in prefix_set:
            if row[u]:
                card[v] += 1

    rest = list(remaining)
    out = []
    while rest:
        best = max(card[v] for v in rest)
        v = min(w for w in rest if card[w] == best)
        out.append(v)
        rest.remove(v)
        row = graph[v]
        for u in rest:
            if row[u]:
                card[u] += 1
    return out


def _recompute(graph, ordering, k):
    """Keep ordering[:k] fixed and re-derive ordering[k:] greedily."""
    prefix = ordering[:k]
    suffix = _mcs_suffix(graph, prefix, ordering[k:])
    return prefix + suffix


def init(graph):
    n = len(graph)
    return {"ordering": _mcs_suffix(graph, [], list(range(n)))}


def insert_edge(graph, edge, state):
    a, b = edge
    ordering = state["ordering"]
    pos = {v: i for i, v in enumerate(ordering)}
    x, y = (a, b) if pos[a] < pos[b] else (b, a)
    return {"ordering": _recompute(graph, ordering, pos[x] + 1)}


def delete_edge(graph, edge, state):
    a, b = edge
    ordering = state["ordering"]
    pos = {v: i for i, v in enumerate(ordering)}
    x, y = (a, b) if pos[a] < pos[b] else (b, a)
    return {"ordering": _recompute(graph, ordering, pos[y])}
