"""Dynamic LexBFS ordering (open problem tier).

Strategy: maintain a valid LexBFS ordering. On each update, first try a
cheap local repair (reorder the affected vertex within its current
position, or a small local re-derivation); if the repair cannot certify
validity, fall back to a full O(n^2) partition-refinement LexBFS
recomputation.

Validity is certified by the (LB) 4-point property of Corneil & Krueger:
for all positions a < b < c with ac in E and ab not in E, there exists
d < a with db in E and dc not in E.
"""


def _adj_sets(graph):
    n = len(graph)
    adj = [set() for _ in range(n)]
    for u in range(n):
        row = graph[u]
        for v in range(u + 1, n):
            if row[v]:
                adj[u].add(v)
                adj[v].add(u)
    return adj


def _is_valid_lexbfs(order, adj):
    """Certify via the (LB) 4-point property. O(n^3) worst case but
    usually fast; used only as a cheap check on small n or after repair."""
    n = len(order)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    for a in range(n):
        va = order[a]
        for b in range(a + 1, n):
            vb = order[b]
            if vb in adj[va]:
                continue
            # ab not in E; need: for all c > b with ac in E, exists d < a
            # with db in E and dc not in E.
            for c in range(b + 1, n):
                vc = order[c]
                if vc not in adj[va]:
                    continue
                # need d < a with db in E and dc not in E
                ok = False
                for d in range(a):
                    vd = order[d]
                    if vb in adj[vd] and vc not in adj[vd]:
                        ok = True
                        break
                if not ok:
                    return False
    return True


def _lexbfs_full_simple(adj):
    """Simple O(n^2) LexBFS using bitset labels (correct, clear).

    Maintains a partition of the unprocessed vertices into buckets, each
    bucket holding vertices with the same label (the set of already-
    processed neighbours).  When a vertex v is selected, every bucket is
    split into (bucket ∩ N(v), bucket \\ N(v)) and the partition is
    re-sorted by label so that the front bucket is the one with the
    lexicographically largest label (most processed neighbours first).
    The next vertex is taken from the front bucket.
    """
    n = len(adj)
    adjb = [0] * n
    for u in range(n):
        b = 0
        for v in adj[u]:
            b |= 1 << v
        adjb[u] = b

    # label[v] = bitset of already-processed vertices adjacent to v
    label = [0] * n
    # buckets: list of lists, front to back
    buckets = [[v] for v in range(n)]
    order = []
    while True:
        while buckets and not buckets[0]:
            buckets.pop(0)
        if not buckets:
            break
        v = buckets[0].pop(0)
        order.append(v)
        # update labels: v is now processed
        for x in range(n):
            if x != v and (adjb[v] >> x) & 1:
                label[x] |= 1 << v
        new_buckets = []
        for bucket in buckets:
            if not bucket:
                continue
            inb = [x for x in bucket if (adjb[v] >> x) & 1]
            outb = [x for x in bucket if not ((adjb[v] >> x) & 1)]
            if inb and outb:
                new_buckets.append(inb)
                new_buckets.append(outb)
            else:
                new_buckets.append(bucket)
        # sort buckets by label (lexicographically largest first)
        new_buckets.sort(key=lambda b: label[b[0]], reverse=True)
        buckets = new_buckets
    return order


def _try_local_repair(order, adj, u, v, edge_inserted):
    """Try to fix the ordering by moving one of {u, v} to a new position.
    Returns a new order if valid, else None."""
    n = len(order)
    pos = [0] * n
    for i, x in enumerate(order):
        pos[x] = i
    candidates = []
    for mv in (u, v):
        # try moving mv to each position
        rest = [x for x in order if x != mv]
        for p in range(n):
            new_order = rest[:p] + [mv] + rest[p:]
            if _is_valid_lexbfs(new_order, adj):
                return new_order
    return None


def _verify_order(order, adj):
    """Sanity check: if the order is not a valid LexBFS, recompute."""
    if not _is_valid_lexbfs(order, adj):
        return _lexbfs_full_simple(adj)
    return order


def init(graph):
    adj = _adj_sets(graph)
    order = _lexbfs_full_simple(adj)
    return {'ordering': order, 'adj': adj}


def insert_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].add(v)
    adj[v].add(u)
    order = state['ordering']
    # try cheap local repair
    new_order = _try_local_repair(order, adj, u, v, True)
    if new_order is None:
        new_order = _lexbfs_full_simple(adj)
    new_order = _verify_order(new_order, adj)
    return {'ordering': new_order, 'adj': adj}


def delete_edge(graph, edge, state):
    u, v = edge
    adj = state['adj']
    adj[u].discard(v)
    adj[v].discard(u)
    order = state['ordering']
    new_order = _try_local_repair(order, adj, u, v, False)
    if new_order is None:
        new_order = _lexbfs_full_simple(adj)
    new_order = _verify_order(new_order, adj)
    return {'ordering': new_order, 'adj': adj}
