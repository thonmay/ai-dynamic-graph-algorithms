# dynamic_mcs (undirected): maintain a Maximal Cardinality Search ordering.
# Approach: partial recompute from the first position whose backward-degree
# may have changed, keeping the valid prefix fixed. On insertion, the later
# endpoint's backward degree increases, so we recompute from min(pos)+1.
# On deletion, it decreases, so we recompute from max(pos).
# Tie-breaking: lowest vertex id (matching the offline oracle).

def _mcs_suffix(graph, prefix, start):
    """Recompute MCS ordering from position *start*, keeping prefix[:start]."""
    n = len(graph)
    chosen = set(prefix[:start])
    card = [0] * n
    for w in chosen:
        for u in range(n):
            if graph[w][u] == 1 and u not in chosen:
                card[u] += 1
    ordering = list(prefix[:start])
    remaining = [v for v in range(n) if v not in chosen]
    while remaining:
        best = max(card[v] for v in remaining)
        pick = min(v for v in remaining if card[v] == best)
        ordering.append(pick)
        chosen.add(pick)
        remaining.remove(pick)
        for u in range(n):
            if graph[pick][u] == 1 and u not in chosen:
                card[u] += 1
    return ordering


def init(graph):
    ordering = _mcs_suffix(graph, [], 0)
    position = {v: i for i, v in enumerate(ordering)}
    graph_copy = [row[:] for row in graph]
    return {'ordering': ordering, 'position': position, 'graph': graph_copy}


def insert_edge(graph, edge, state):
    u, v = edge
    if u == v or state['graph'][u][v] == 1:
        return state
    state['graph'][u][v] = 1
    state['graph'][v][u] = 1
    start = min(state['position'][u], state['position'][v]) + 1
    ordering = _mcs_suffix(graph, state['ordering'], start)
    state['ordering'] = ordering
    state['position'] = {v: i for i, v in enumerate(ordering)}
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    if u == v or state['graph'][u][v] == 0:
        return state
    state['graph'][u][v] = 0
    state['graph'][v][u] = 0
    start = max(state['position'][u], state['position'][v])
    ordering = _mcs_suffix(graph, state['ordering'], start)
    state['ordering'] = ordering
    state['position'] = {v: i for i, v in enumerate(ordering)}
    return state
