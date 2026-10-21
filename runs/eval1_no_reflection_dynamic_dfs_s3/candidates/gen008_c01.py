"""Dynamic DFS forest from fixed root 0 under edge insertions/deletions.

Maintains a genuine DFS forest (parent, discover, finish) of the current
graph.  A spanning tree is a DFS tree iff it has no forward-cross edge
(Yang et al., Lemma 1), so after an update we only need to check whether
the update created a forward-cross edge or removed a tree edge.

- Insertion: if the new edge u->v is a forward-cross edge w.r.t. the
  current forest, or if v was previously unreachable (the new edge makes
  v reachable, so the forest must be extended), re-run DFS from scratch;
  otherwise the forest stays valid (reachability only grows, so
  previously-reachable vertices keep their ancestor relations).
- Deletion: if the deleted edge is a tree edge, re-run DFS from scratch;
  otherwise the forest stays valid (removing a non-tree edge cannot
  create a forward-cross edge, and the tree edges are unchanged).

Re-running DFS is O(n^2) in the matrix representation, same as the
offline algorithm; the dynamic checks avoid it in the common case.
"""


def _dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    # Iterative DFS with an explicit stack of (vertex, next-neighbor)
    # frames; equivalent to the recursive version but without recursion
    # depth limits on large graphs.
    stack = [(0, 0)]
    discover[0] = counter[0]
    counter[0] += 1
    while stack:
        u, w = stack[-1]
        if w < n:
            stack[-1] = (u, w + 1)
            if graph[u][w] and discover[w] == -1:
                parent[w] = u
                discover[w] = counter[0]
                counter[0] += 1
                stack.append((w, 0))
        else:
            finish[u] = counter[0]
            counter[0] += 1
            stack.pop()
    return parent, discover, finish


def _is_ancestor(u, v, discover, finish):
    return discover[u] <= discover[v] and finish[v] <= finish[u]


def _is_forward_cross(u, v, discover, finish):
    # edge u->v is a forward-cross edge iff u discovered before v and
    # neither is an ancestor of the other.
    if discover[u] == -1 or discover[v] == -1:
        return False
    if discover[u] < discover[v]:
        return not _is_ancestor(u, v, discover, finish)
    return False


def init(graph):
    parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def insert_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    # The new edge u->v must be a tree edge, forward edge or back edge
    # w.r.t. the current forest.  If v is undiscovered, or u is discovered
    # before v but neither is an ancestor of the other (forward-cross),
    # the forest is no longer a DFS forest: re-run DFS from scratch.
    #
    # Note: if u is undiscovered, the edge cannot be a forward-cross edge
    # (u is not reachable from the root, so no reachable vertex can be
    # discovered before it), and v is reachable only if it was already
    # reachable, so the forest stays valid.
    if discover[v] == -1 or _is_forward_cross(u, v, discover, finish):
        parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }


def delete_edge(graph, edge, state):
    u, v = edge
    parent = state['parent']
    discover = state['discover']
    finish = state['finish']
    if parent[v] == u:
        parent, discover, finish = _dfs(graph)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
