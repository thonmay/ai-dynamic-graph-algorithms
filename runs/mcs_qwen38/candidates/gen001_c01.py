"""Dynamic MCS (undirected): maintain a valid maximal-cardinality-search ordering.

Approach: fully dynamic recompute. After each edge update the graph argument
already reflects the change, so we recompute the MCS ordering from scratch on
the current graph. This is the offline MCS algorithm applied to the current
graph, which guarantees the invariant (each chosen vertex has maximum
cardinality among the unchosen) holds after every operation.

State: dict with key "ordering" -> list of vertex ids (a permutation of 0..n-1).
"""


def _mcs_ordering(graph):
    """Compute a valid MCS ordering of the undirected graph from scratch.

    Ties are broken by lowest vertex id, matching the offline reference.
    """
    n = len(graph)
    chosen = [False] * n
    cardinality = [0] * n
    ordering = []

    for _ in range(n):
        # Select the unchosen vertex with maximum cardinality (lowest id on ties).
        best = -1
        best_card = -1
        for u in range(n):
            if not chosen[u] and cardinality[u] > best_card:
                best_card = cardinality[u]
                best = u
        if best < 0:
            break
        ordering.append(best)
        chosen[best] = True
        # Bump the cardinality of every unchosen neighbor of best.
        for u in range(n):
            if not chosen[u] and graph[best][u] == 1:
                cardinality[u] += 1

    return ordering


def init(graph):
    """Build the initial state from the starting adjacency matrix."""
    return {"ordering": _mcs_ordering(graph)}


def insert_edge(graph, edge, state):
    """Update state after inserting edge (u, v). graph already includes it."""
    return {"ordering": _mcs_ordering(graph)}


def delete_edge(graph, edge, state):
    """Update state after deleting edge (u, v). graph already excludes it."""
    return {"ordering": _mcs_ordering(graph)}
