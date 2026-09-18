# dynamic_mcs (undirected): maintain a Maximal Cardinality Search ordering.
# Naive fully-dynamic approach: recompute MCS from scratch on every edge update.
# State: {"ordering": [v1, v2, ..., vn]}


def _mcs(graph):
    """Compute MCS ordering: at each step pick the unchosen vertex with
    maximum cardinality (already-chosen neighbors), tie-break lowest id."""
    n = len(graph)
    chosen = [False] * n
    cardinality = [0] * n
    ordering = []
    for _ in range(n):
        best_v = -1
        best_card = -1
        for v in range(n):
            if not chosen[v] and cardinality[v] > best_card:
                best_card = cardinality[v]
                best_v = v
        ordering.append(best_v)
        chosen[best_v] = True
        for u in range(n):
            if graph[best_v][u] == 1 and not chosen[u]:
                cardinality[u] += 1
    return ordering


def init(graph):
    return {"ordering": _mcs(graph)}


def insert_edge(graph, edge, state):
    return {"ordering": _mcs(graph)}


def delete_edge(graph, edge, state):
    return {"ordering": _mcs(graph)}
