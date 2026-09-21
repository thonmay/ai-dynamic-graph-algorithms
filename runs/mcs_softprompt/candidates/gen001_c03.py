"""Dynamic MCS (undirected): maintain a valid maximal-cardinality-search
ordering under single-edge insertions and deletions.

Approach: keep the current ordering. A single edge flip can only break the
greedy (max-cardinality) property from a certain point onward, so the prefix
stays valid and only the suffix is re-derived:
  - insert (x,y) with pos[x] < pos[y]: at step pos[x]+1 the first unchosen
    vertex (y) gains an earlier neighbor (x), so recompute from pos[x]+1.
  - delete (x,y) with pos[x] < pos[y]: the chosen vertex first loses
    cardinality at y's own selection, pos[y], so recompute from pos[y].
The suffix is re-derived with a max-heap greedy (max cardinality, ties by
lowest vertex id), which beats a full O(n^2) scan when the suffix is long.
The maintained ordering always satisfies the MCS invariant: every vertex is
chosen while its cardinality (number of already-chosen neighbors) is maximal
among the not-yet-chosen vertices.
"""

import heapq


def _mcs_full(adj):
    """Full MCS ordering of the whole graph via a max-heap greedy.

    Ties on cardinality are broken by lowest vertex id.
    """
    n = len(adj)
    card = [0] * n
    heap = [(0, v) for v in range(n)]
    heapq.heapify(heap)
    remaining = set(range(n))
    out = []
    while remaining:
        _negc, v = heapq.heappop(heap)
        if v not in remaining:
            continue
        remaining.discard(v)
        out.append(v)
        for u in adj[v]:
            if u in remaining:
                card[u] += 1
                heapq.heappush(heap, (-card[u], u))
    return out


def _recompute_suffix(adj, ordering, k):
    """Keep ordering[:k] fixed; re-derive ordering[k:] with a heap greedy.

    Each remaining vertex starts with cardinality equal to its number of
    neighbors in the fixed prefix; the greedy then proceeds as usual.
    """
    prefix_set = set(ordering[:k])
    remaining = ordering[k:]
    card = {v: 0 for v in remaining}
    for v in remaining:
        for u in adj[v]:
            if u in prefix_set:
                card[v] += 1
    heap = [(-card[v], v) for v in remaining]
    heapq.heapify(heap)
    rem_set = set(remaining)
    out = []
    while rem_set:
        _negc, v = heapq.heappop(heap)
        if v not in rem_set:
            continue
        rem_set.discard(v)
        out.append(v)
        for u in adj[v]:
            if u in rem_set:
                card[u] += 1
                heapq.heappush(heap, (-card[u], u))
    return ordering[:k] + out


def _make_pos(ordering):
    pos = [0] * len(ordering)
    for i, v in enumerate(ordering):
        pos[v] = i
    return pos


def init(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    ordering = _mcs_full(adj)
    return {"ordering": ordering, "pos": _make_pos(ordering), "adj": adj}


def insert_edge(graph, edge, state):
    a, b = edge
    adj = state["adj"]
    adj[a].add(b)
    adj[b].add(a)
    pos = state["pos"]
    ordering = state["ordering"]
    x, y = (a, b) if pos[a] < pos[b] else (b, a)
    new_ordering = _recompute_suffix(adj, ordering, pos[x] + 1)
    return {"ordering": new_ordering, "pos": _make_pos(new_ordering), "adj": adj}


def delete_edge(graph, edge, state):
    a, b = edge
    adj = state["adj"]
    adj[a].discard(b)
    adj[b].discard(a)
    pos = state["pos"]
    ordering = state["ordering"]
    x, y = (a, b) if pos[a] < pos[b] else (b, a)
    new_ordering = _recompute_suffix(adj, ordering, pos[y])
    return {"ordering": new_ordering, "pos": _make_pos(new_ordering), "adj": adj}
