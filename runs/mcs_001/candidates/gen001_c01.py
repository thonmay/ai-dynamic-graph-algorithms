"""Dynamic MCS (undirected): maintain a valid MCS ordering under edge updates.

Approach: fully dynamic via recompute. The update handler receives the
after-graph, so we recompute the MCS ordering from scratch (the offline
algorithm) on every insert/delete. A single edge flip can change the
ordering non-locally, so recompute is the safe correct strategy.
Tie-break: lowest vertex id. State = {"ordering": [...]}.
"""


def _mcs(graph):
    """Offline MCS: return a valid MCS ordering of the undirected graph."""
    n = len(graph)
    chosen = [False] * n
    cardinality = [0] * n
    ordering = []
    for _ in range(n):
        unchosen = [u for u in range(n) if not chosen[u]]
        if not unchosen:
            break
        max_card = max(cardinality[u] for u in unchosen)
        v = min(u for u in unchosen if cardinality[u] == max_card)
        ordering.append(v)
        chosen[v] = True
        for u in range(n):
            if graph[v][u] == 1 and not chosen[u]:
                cardinality[u] += 1
    return ordering


def init(graph):
    return {"ordering": _mcs(graph)}


def insert_edge(graph, edge, state):
    return {"ordering": _mcs(graph)}


def delete_edge(graph, edge, state):
    return {"ordering": _mcs(graph)}
