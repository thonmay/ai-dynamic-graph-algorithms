"""Dynamic DFS forest maintenance (directed, root 0).

A single edge flip only invalidates the maintained DFS forest in a local way,
so most updates are answered by keeping the existing forest untouched:

- Insert u->v: the old forest is still a DFS forest unless the new edge
  (a) makes a previously unreachable vertex reachable, or
  (b) is a forward-cross edge (u discovered before v, v not a descendant of u).
- Delete u->v: the old forest is still a DFS forest unless u->v is a tree
  edge (parent[v] == u), which dangles v's parent. A deleted non-tree edge
  never creates a forward-cross edge, and every remaining vertex stays
  reachable through its tree path (the tree is a subgraph of the graph).

When the forest is affected we rebuild it from scratch (always correct); the
cheap path is taken for the common case. The certificate the verifier reads
is parent + discover + finish, with the no-forward-cross property.
"""

ROOT = 0


def _dfs(graph, start, parent, discover, finish):
    """Iterative DFS over the reachable set from `start` in `graph`.

    Fills parent/discover/finish for the newly reached vertices and returns
    the set of vertices it visited. Neighbours are scanned in increasing
    order, matching a standard recursive DFS.
    """
    n = len(graph)
    visited = set()
    timer = [0]
    stack = [(start, 0)]
    parent[start] = None
    discover[start] = 0
    visited.add(start)
    while stack:
        u, idx = stack[-1]
        row = graph[u]
        advanced = False
        while idx < n:
            v = idx
            idx += 1
            if row[v] == 1 and v not in visited:
                parent[v] = u
                discover[v] = timer[0]
                timer[0] += 1
                visited.add(v)
                stack[-1] = (u, idx)
                stack.append((v, 0))
                advanced = True
                break
        if not advanced:
            finish[u] = timer[0]
            timer[0] += 1
            stack.pop()
    return visited


def _rebuild(graph):
    """Full DFS forest of `graph` from the root."""
    n = len(graph)
    parent = [None] * n
    discover = [None] * n
    finish = [None] * n
    _dfs(graph, ROOT, parent, discover, finish)
    return {"parent": parent, "discover": discover, "finish": finish}


def init(graph):
    return _rebuild(graph)


def _is_descendant(discover, finish, u, v):
    """True if v is a descendant of u (u discovered before v, v finished before u)."""
    return discover[u] < discover[v] < finish[v] < finish[u]


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state["parent"]
    discover = state["discover"]
    finish = state["finish"]

    u_reach = discover[u] is not None
    v_reach = discover[v] is not None

    # (a) v becomes newly reachable (u reachable, v was not): the old forest
    # no longer spans the reachable set.
    if u_reach and not v_reach:
        return _rebuild(graph)

    # (b) u->v is a forward-cross edge: both reachable, u discovered before v,
    # but v is not a descendant of u. (If v is an ancestor of u it is a back
    # edge, fine; if u is unreachable the edge is not part of the forest.)
    if (u_reach and v_reach and discover[u] < discover[v]
            and not _is_descendant(discover, finish, u, v)):
        return _rebuild(graph)

    # Otherwise the old forest is still a valid DFS forest of the new graph.
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state["parent"]

    # Only a deleted tree edge invalidates the forest (it dangles v's parent).
    if v != ROOT and parent[v] == u:
        return _rebuild(graph)

    return state
