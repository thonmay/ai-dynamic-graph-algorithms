# dynamic_bfs (directed): maintain a BFS tree from root 0.
# Approach: apply the edge change in place, then recompute BFS from scratch.

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
    u, v = edge
    graph[u][v] = 1  # idempotent: apply the insert in place before recomputing
    return _bfs(graph)


def delete_edge(graph, edge, state):
    u, v = edge
    graph[u][v] = 0  # idempotent: apply the delete in place before recomputing
    return _bfs(graph)
