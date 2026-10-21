"""Dynamic algorithm candidate. Edit this file; keep the three functions."""


def _full_dfs(graph, n):
    """Standard DFS from root 0 with a shared counter (mirrors the offline
    baseline exactly). Returns (parent, discover, finish) as dicts."""
    parent = {i: None for i in range(n)}
    discover = {}
    finish = {}
    visited = set()
    timer = [0]

    def dfs(u):
        visited.add(u)
        discover[u] = timer[0]
        timer[0] += 1
        for v in range(n):
            if graph[u][v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1

    dfs(0)
    return parent, discover, finish


def init(graph):
    n = len(graph)
    parent, discover, finish = _full_dfs(graph, n)
    return {"parent": parent, "discover": discover, "finish": finish, "n": n}


def insert_edge(graph, edge, state):
    n = state["n"]
    parent, discover, finish = _full_dfs(graph, n)
    return {"parent": parent, "discover": discover, "finish": finish, "n": n}


def delete_edge(graph, edge, state):
    n = state["n"]
    parent, discover, finish = _full_dfs(graph, n)
    return {"parent": parent, "discover": discover, "finish": finish, "n": n}
