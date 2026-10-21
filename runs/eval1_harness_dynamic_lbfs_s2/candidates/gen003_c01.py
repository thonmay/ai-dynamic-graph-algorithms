"""Dynamic algorithm candidate. Edit this file; keep the three functions.

Strategy: recompute a valid LexBFS ordering from scratch after every update,
using the fastest correct partition-refinement LexBFS (single pass per cell,
no per-step neighbour set). A keep-if-valid variant was measured to cost more
than this recompute (the (LB) validity check is O(n^2) with a larger constant
than the recompute), so the fastest recompute minimises work_ratio.
"""


def _lexbfs(graph):
    """Partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

    Starts at vertex 0 with the minimum-id tie-break. Returns a valid
    LexBFS ordering of the undirected graph given as a 0/1 adjacency matrix.
    """
    n = len(graph)
    Pi = [list(range(n))]
    order = []
    for _ in range(n):
        p = Pi[0][0]
        order.append(p)
        if len(Pi[0]) == 1:
            Pi = Pi[1:]
        else:
            Pi[0] = Pi[0][1:]
        row = graph[p]
        newPi = []
        for C in Pi:
            a = []
            b = []
            for v in C:
                if row[v]:
                    a.append(v)
                else:
                    b.append(v)
            if a:
                newPi.append(a)
            if b:
                newPi.append(b)
        Pi = newPi
    return order


def init(graph):
    return {"ordering": _lexbfs(graph)}


def insert_edge(graph, edge, state):
    return {"ordering": _lexbfs(graph)}


def delete_edge(graph, edge, state):
    return {"ordering": _lexbfs(graph)}
