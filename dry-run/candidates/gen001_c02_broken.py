# dynamic_bfs (directed): maintain a BFS tree from root 0.
# BROKEN: does not recompute on edge insertion, so tree becomes stale.

ROOT = 0


def _bfs(graph):
    n = len(graph)
    dist = {ROOT: 0}
    parent = {}
    queue = [ROOT]
    while queue:
        u = queue.pop(0)
        for v in range(n):
            if graph[u][v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {'parent': parent, 'dist': dist}


def init(graph):
    return _bfs(graph)


def insert_edge(graph, edge, state):
    # BUG: returns old state without recomputing
    return state


def delete_edge(graph, edge, state):
    # BUG: returns old state without recomputing
    return state
