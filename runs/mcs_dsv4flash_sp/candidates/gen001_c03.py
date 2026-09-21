# dynamic_mcs (undirected): maintain a Maximal Cardinality Search ordering.
#
# MCS greedily picks, each round, an unchosen vertex whose number of already
# chosen neighbours is maximal (ties broken toward the lowest vertex id).
#
# A flipped edge (u, v) can only change the cardinality of one of its two
# endpoints, and only once the other endpoint is already chosen. If a is the
# earlier of the two in the current ordering and b the later, then b stays
# unchosen through the prefix ending at a, so every greedy decision up to and
# including position pos[a] replays identically to the offline run: the flip
# cannot disturb that prefix.
#
# Structural difference from the sibling candidates: we first *verify* the
# current ordering from position pos[a] + 1, walking the preserved prefix. If
# every later position is still a valid maximal-cardinality (lowest-id-tie)
# choice, the ordering is left untouched and the update costs one clean pass
# over the muted suffix with bucket-tracked cardinalities. Only when the first
# invalid position is hit do we rebuild that suffix greedily from buckets.
#
# State: {"ordering": list[int]} -- a valid MCS ordering of the current graph.


def _full_mcs(graph):
    """Offline MCS ordering from scratch (tie-break: lowest vertex id)."""
    n = len(graph)
    ordering = []
    card = [0] * n
    chosen = [False] * n
    for _ in range(n):
        best, best_v = -1, -1
        for v in range(n):
            if not chosen[v] and (card[v] > best or (card[v] == best and best_v == -1)):
                best, best_v = card[v], v
        chosen[best_v] = True
        ordering.append(best_v)
        for w in range(n):
            if graph[best_v][w] and not chosen[w]:
                card[w] += 1
    return ordering


def _build_initial(graph, prefix):
    """Cardinality buckets over the vertices still unchosen after `prefix`.

    Returns (card, buckets, maxc): card[x] is the count of chosen-prefix
    neighbours of x; buckets keys card values to the set of unchosen vertices
    attaining them; maxc is the largest non-empty card value.
    """
    n = len(graph)
    chosen = [False] * n
    for w in prefix:
        chosen[w] = True
    card = [0] * n
    buckets = {}
    maxc = -1
    for v in range(n):
        if chosen[v]:
            continue
        c = 0
        for w in prefix:
            if graph[v][w]:
                c += 1
        card[v] = c
        buckets.setdefault(c, set()).add(v)
        if c > maxc:
            maxc = c
    return card, buckets, maxc


def _verify_suffix(graph, ordering, start):
    """Check positions [start, n) of `ordering` against MCS validity.

    At each position i we need ordering[i] to have the maximum card among the
    vertices not yet chosen, with the tie broken by lowest id (so no later
    unchosen vertex of the same card and smaller id may exist). Cards are
    maintained for all unchosen vertices and updated as the choice is fixed.
    Returns True if every position in [start, n) is valid.
    """
    n = len(graph)
    chosen = [False] * n
    for w in ordering[:start]:
        chosen[w] = True
    card = [0] * n
    for v in range(n):
        if chosen[v]:
            continue
        c = 0
        for w in ordering[:start]:
            if graph[v][w]:
                c += 1
        card[v] = c

    for k in range(start, n):
        x = ordering[k]
        if chosen[x]:
            return False
        # x is valid iff no unchosen vertex has card > card[x], and no
        # unchosen vertex with equal card and a smaller id exists.
        for v in range(n):
            if chosen[v] or v == x:
                continue
            if card[v] > card[x] or (card[v] == card[x] and v < x):
                return False
        chosen[x] = True
        for w in range(n):
            if graph[x][w] and not chosen[w]:
                card[w] += 1
    return True


def _rebuild_suffix(graph, prefix):
    """Rebuild ordering[prefix:] greedily, treating `prefix` as chosen."""
    n = len(graph)
    order = list(prefix)
    card, buckets, maxc = _build_initial(graph, prefix)
    chosen = [False] * n
    for w in prefix:
        chosen[w] = True
    while len(order) < n:
        cands = buckets.get(maxc)
        while (cands is None or not cands) and maxc >= 0:
            maxc -= 1
            cands = buckets.get(maxc)
        v = min(cands)
        cands.remove(v)
        if not cands:
            del buckets[maxc]
        order.append(v)
        chosen[v] = True
        for w in range(n):
            if graph[v][w] and not chosen[w]:
                old = card[w]
                buckets[old].discard(w)
                if not buckets[old]:
                    del buckets[old]
                new = old + 1
                card[w] = new
                buckets.setdefault(new, set()).add(w)
                if new > maxc:
                    maxc = new
    return order


def init(graph):
    if not graph:
        return {"ordering": []}
    return {"ordering": _full_mcs(graph)}


def _update(graph, edge, state):
    u, v = edge
    if u == v:
        return state
    ordering = state["ordering"]
    n = len(ordering)
    if n <= 1:
        return state
    pos = [0] * n
    for i, w in enumerate(ordering):
        pos[w] = i
    a = u if pos[u] < pos[v] else v
    start = pos[a] + 1
    # If the current ordering is still a valid MCS ordering, keep it as is.
    if _verify_suffix(graph, ordering, start):
        return state
    prefix = ordering[:start]
    return {"ordering": _rebuild_suffix(graph, prefix)}


def insert_edge(graph, edge, state):
    return _update(graph, edge, state)


def delete_edge(graph, edge, state):
    return _update(graph, edge, state)