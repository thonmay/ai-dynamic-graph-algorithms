"""Dynamic BFS tree from fixed root 0 under directed edge insert/delete.

State: dict with
  'n'      : number of vertices
  'dist'   : list, BFS distance from root, -1 if unreachable
  'parent' : list, parent in BFS tree, -1 if unreachable (root parent -1)
  'tree'   : list of lists, tree children (out-edges of the BFS tree)
  'adj'    : list of sets, current out-neighbors (kept in sync with graph)

Insertion: if the new edge (u,v) gives v a shorter distance (dist[u]+1 <
dist[v]), re-parent v and cascade the improvement to v's subtree. Otherwise
the existing tree is still a valid BFS tree.

Deletion: if the deleted edge is not the tree edge of v, nothing changes.
Otherwise the subtree of v may be broken: BFS from the frontier of
dist[v]-1 (all vertices at that distance, which are unaffected) restricted
to the subtree re-attaches every still-reachable vertex; the rest becomes
unreachable.
"""

from collections import deque


def _refresh_result(state):
    n = state['n']
    dist = state['dist']
    parent = state['parent']
    state['result'] = {'distances': {i: dist[i] for i in range(n)},
                       'parent': {i: (None if parent[i] == -1 else parent[i])
                                  for i in range(n)}}
    state['distances'] = {i: dist[i] for i in range(n)}
    state['parent'] = {i: (None if parent[i] == -1 else parent[i])
                       for i in range(n)}


def _bfs_from_frontier(n, adj, frontier, dist, parent, tree):
    """BFS starting from `frontier` (all at distance d0 = dist[frontier[0]]).

    Only vertices whose current dist is > d0 may be re-parented; others are
    treated as already settled. Mutates dist/parent/tree in place.
    """
    if not frontier:
        return
    d0 = dist[frontier[0]]
    q = deque()
    for x in frontier:
        q.append(x)
    while q:
        u = q.popleft()
        du = dist[u]
        for w in adj[u]:
            if dist[w] <= du:
                continue  # already settled at <= du (or unreachable but closer)
            if dist[w] != du + 1:
                # w was unreachable or farther: attach it
                if dist[w] != -1:
                    oldp = parent[w]
                    if oldp != -1:
                        tree[oldp].remove(w)
                dist[w] = du + 1
                parent[w] = u
                tree[u].append(w)
            q.append(w)


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(n):
            if row[v]:
                adj[u].add(v)
    dist = [-1] * n
    parent = [-1] * n
    tree = [[] for _ in range(n)]
    dist[0] = 0
    q = deque([0])
    while q:
        u = q.popleft()
        for w in adj[u]:
            if dist[w] == -1:
                dist[w] = dist[u] + 1
                parent[w] = u
                tree[u].append(w)
                q.append(w)
    _refresh_result(state)
    return state


def insert_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].add(v)
    du = state['dist'][u]
    dv = state['dist'][v]
    if du == -1 or du + 1 >= dv:
        # no improvement possible (or v already at/below this distance)
        return state
    # v gets a shorter distance: re-parent v and cascade
    oldp = state['parent'][v]
    if oldp != -1:
        state['tree'][oldp].remove(v)
    state['dist'][v] = du + 1
    state['parent'][v] = u
    state['tree'][u].append(v)
    # cascade: BFS from v; any descendant whose distance can be improved
    # via the new path gets re-parented.
    _bfs_from_frontier(state['n'], state['adj'], [v], state['dist'],
                       state['parent'], state['tree'])
    _refresh_result(state)
    return state


def delete_edge(graph, edge, state):
    u, v = edge
    state['adj'][u].discard(v)
    if state['parent'][v] != u:
        # not a tree edge: tree unchanged, still valid
        _refresh_result(state)
        return state
    n = state['n']
    dist = state['dist']
    parent = state['parent']
    tree = state['tree']
    old_dv = dist[v]
    # collect subtree of v (in the current tree)
    subtree = []
    stack = [v]
    while stack:
        x = stack.pop()
        subtree.append(x)
        stack.extend(tree[x])
    in_sub = set(subtree)
    # detach subtree from its parents
    for x in subtree:
        p = parent[x]
        if p != -1 and p not in in_sub:
            tree[p].remove(x)
        parent[x] = -1
        dist[x] = -1
    # frontier: all vertices at distance old_dv - 1 (outside the subtree,
    # since tree edges always go from d to d+1)
    if old_dv == 0:
        # v was the root: nothing reachable anymore
        _refresh_result(state)
        return state
    frontier = [w for w in range(n) if dist[w] == old_dv - 1]
    _bfs_from_frontier(n, state['adj'], frontier, dist, parent, tree)
    _refresh_result(state)
    return state
