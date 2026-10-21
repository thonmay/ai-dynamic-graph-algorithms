"""Dynamic algorithm candidate. Edit this file; keep the three functions."""


def _lexbfs(graph):
    """Partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).

    Starts at vertex 0 with the minimum-id tie-break. Returns a valid
    LexBFS ordering of the undirected graph given as a 0/1 adjacency matrix.
    """
    n = len(graph)
    # Pi: ordered list of cells; each cell is a list of vertices.
    Pi = [list(range(n))]
    order = []
    for _ in range(n):
        p = Pi[0][0]
        order.append(p)
        # Remove p from its cell (it is the first element).
        if len(Pi[0]) == 1:
            Pi = Pi[1:]
        else:
            Pi[0] = Pi[0][1:]
        # Refine every remaining cell by adjacency to p: the neighbor part
        # precedes the non-neighbor part.
        row = graph[p]
        newPi = []
        for C in Pi:
            a = [v for v in C if row[v]]
            b = [v for v in C if not row[v]]
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
