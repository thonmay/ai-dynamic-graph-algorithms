# dynamic_mcs (undirected): maintain a Maximal Cardinality Search ordering.
# Approach: an edge update between u and v changes only the cardinality of u
# and v, and only once the other endpoint is already chosen. Hence the MCS
# ordering is unchanged up to start = min(pos[u], pos[v]); only the suffix
# starting there needs to be recomputed. Prefix is kept, suffix rebuilt greedily.
#
# State: {"ordering": list[int]} - a valid MCS ordering of the current graph.


def _mcs(graph):
    """Full MCS ordering from scratch (tie-break: lowest vertex id)."""
    n = len(graph)
    chosen = set()
    card = [0] * n
    ordering = []
    for _ in range(n):
        best = -1
        best_v = -1
        for v in range(n):
            if v in chosen:
                continue
            if best_v == -1 or card[v] > best or (card[v] == best and v < best_v):
                best = card[v]
                best_v = v
        chosen.add(best_v)
        ordering.append(best_v)
        for w in range(n):
            if graph[best_v][w] and w not in chosen:
                card[w] += 1
    return ordering


def _repair_suffix(graph, ordering, start):
    """Rebuild ordering[start:] greedily from the (unchanged) chosen prefix."""
    n = len(graph)
    prefix = ordering[:start]
    chosen = set(prefix)
    # cardinality of each vertex relative to the chosen prefix in current graph
    card = [0] * n
    for x in range(n):
        c = 0
        for ch in prefix:
            if graph[x][ch]:
                c += 1
        card[x] = c
    new_ordering = list(prefix)
    for _ in range(start, n):
        best = -1
        best_v = -1
        for v in range(n):
            if v in chosen:
                continue
            if best_v == -1 or card[v] > best or (card[v] == best and v < best_v):
                best = card[v]
                best_v = v
        chosen.add(best_v)
        new_ordering.append(best_v)
        for w in range(n):
            if graph[best_v][w] and w not in chosen:
                card[w] += 1
    return new_ordering


def init(graph):
    return {"ordering": _mcs(graph)}


def insert_edge(graph, edge, state):
    u, v = edge
    if u == v:
        return state
    ordering = state["ordering"]
    start = min(ordering.index(u), ordering.index(v))
    return {"ordering": _repair_suffix(graph, ordering, start)}


def delete_edge(graph, edge, state):
    return insert_edge(graph, edge, state)