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
- Deletion: if the deleted edge is a tree edge u->v, only the subtree
  rooted at v is affected: no new forward-cross edge can appear outside
  it (the forest there is unchanged and the removed edge only reduces
  reachability), and the subtree's internal order is recomputed fresh.
  We re-search only that subtree, keeping the untouched vertices'
  discover/finish times.  If the deleted edge is not a tree edge, the
  forest stays valid.

The partial re-search is O(|subtree| * n) in the matrix representation;
the common case (non-tree updates) costs O(1).
"""


def _dfs(graph):
    n = len(graph)
    parent = [None] * n
    discover = [-1] * n
    finish = [-1] * n
    counter = [0]

    def rec(u):
        discover[u] = counter[0]
        counter[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1:
                parent[v] = u
                rec(v)
        finish[u] = counter[0]
        counter[0] += 1

    if n > 0:
        rec(0)
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


def _resubtree(graph, root, parent, discover, finish):
    """Re-run DFS restricted to the subtree rooted at `root` (root's
    parent is kept).  Vertices outside the subtree keep their times;
    vertices inside get fresh times in the range
    [discover[root], finish[root]) so the global order stays consistent.
    """
    n = len(graph)
    lo = discover[root]
    hi = finish[root]
    # Mark the subtree vertices (old times) so the re-search can only
    # claim vertices inside the old subtree.
    in_sub = [False] * n
    stack = [root]
    while stack:
        x = stack.pop()
        in_sub[x] = True
        for y in range(n):
            if in_sub[y]:
                continue
            if discover[y] != -1 and lo <= discover[y] < hi:
                in_sub[y] = True
                stack.append(y)
    # The re-search may only claim vertices that are still reachable from
    # `root` in the current graph (the removed tree edge may have cut some
    # of them off).  BFS from root over the current adjacency.
    reach = [False] * n
    stack = [root]
    reach[root] = True
    while stack:
        x = stack.pop()
        for y in range(n):
            if graph[x][y] and not reach[y]:
                reach[y] = True
                stack.append(y)
    # Reset the subtree vertices.  Vertices that are no longer reachable
    # from root become undiscovered; the rest are re-searched.
    for x in range(n):
        if in_sub[x]:
            discover[x] = -1
            finish[x] = -1
            if x != root:
                parent[x] = None
    counter = [lo]

    def rec(u):
        discover[u] = counter[0]
        counter[0] += 1
        for v in range(n):
            if graph[u][v] and discover[v] == -1 and in_sub[v] and reach[v]:
                parent[v] = u
                rec(v)
        finish[u] = counter[0]
        counter[0] += 1

    rec(root)
    return parent, discover, finish


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
        # Tree edge removed: only the subtree rooted at v is affected.
        parent, discover, finish = _resubtree(graph, v, parent, discover, finish)
    return {
        'parent': parent,
        'discover': discover,
        'finish': finish,
    }
