"""Dynamic LexBFS ordering (candidate gen008_c02).

Derived from gen003_c03.  Same correctness core (static HMPV LexBFS + (LB)
4-point certificate), but the update path is much cheaper:

  * insert_edge(u,v): the new edge (u,v) can only create a violation whose
    antecedent uses the new edge, i.e. triples (a,b,c) with {a,c} = {u,v}
    and b between them in the ordering.  So we check only those triples
    (O(n) antecedents, O(n) witnesses each) instead of the full O(n^4)
    certificate.  If clean, keep the ordering; else recompute.
  * delete_edge(u,v): the only triples whose witness set shrinks are those
    with d in {u,v}.  We check only those (O(n^2) antecedents, O(n)
    witnesses each) instead of the full certificate.  If clean, keep; else
    recompute.
  * init: HMPV partition-refinement LexBFS, plus a cached adjacency bitset
    (int per vertex) so the checks run on bit operations.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement (HMPV). Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []
    P = [list(range(n))]
    S = set()
    order = []

    while len(S) < n:
        idx = None
        for i, B in enumerate(P):
            if B:
                idx = i
                break
        if idx is None:
            break
        B = P[idx]
        v = B[0]
        order.append(v)
        S.add(v)
        B.pop(0)
        new_P = []
        for Bk in P:
            if not Bk:
                continue
            adj = []
            nonadj = []
            for x in Bk:
                if graph[x][v]:
                    adj.append(x)
                else:
                    nonadj.append(x)
            if adj:
                new_P.append(adj)
            if nonadj:
                new_P.append(nonadj)
        P = new_P
    return order


def _adj_bits(graph):
    """Adjacency as a list of ints (bit x set iff edge (v,x))."""
    n = len(graph)
    bits = [0] * n
    for v in range(n):
        row = graph[v]
        b = 0
        for x in range(n):
            if row[x]:
                b |= 1 << x
        bits[v] = b
    return bits


def _valid_insert(bits, order, pos, u, v):
    """Check only the triples whose antecedent uses the newly added edge
    (u,v).  For each b strictly between u and v in the ordering, with
    a = the earlier of u,v and c = the later, we need a witness d < a
    (position) with db in E and dc not in E."""
    pu, pv = pos[u], pos[v]
    if pu > pv:
        pu, pv = pv, pu
        u, v = v, u
    a, c = u, v
    for b in order[pu + 1:pv]:
        need = bits[b] & ~bits[c]
        if not (need & ((1 << pu) - 1)):
            return False
    return True


def _valid_delete(bits, order, pos, u, v):
    """Check only the triples whose witness set lost u or v.  For each
    d in {u,v} and each a after d, for each b after a with ab not in E and
    ac in E, a witness t < a (t != d) with tb in E and tc not in E must
    exist.  (The deleted edge (u,v) cannot appear in the antecedent of a
    surviving triple, so no extra antecedent checks are needed.)"""
    n = len(order)
    for d in (u, v):
        pd = pos[d]
        for i in range(pd + 1, n):
            a = order[i]
            for j in range(i + 1, n):
                b = order[j]
                if bits[a] & (1 << b):
                    continue  # ab in E
                for k in range(j + 1, n):
                    c = order[k]
                    if not (bits[a] & (1 << c)):
                        continue  # ac not in E
                    need = bits[b] & ~bits[c]
                    if not (need & ((1 << i) - 1) & ~(1 << d)):
                        return False
    # The deleted edge (u,v) can also create a NEW violation: a triple
    # (a,b,c) with a,b,c all distinct from u,v, a < b < c, ac in E, ab not
    # in E, whose only witness was d = u or d = v (both db in E and dc not
    # in E).  For each such d, check all triples with a after d.
    for d in (u, v):
        pd = pos[d]
        for i in range(pd + 1, n):
            a = order[i]
            if a == u or a == v:
                continue
            for j in range(i + 1, n):
                b = order[j]
                if b == u or b == v:
                    continue
                if bits[a] & (1 << b):
                    continue  # ab in E
                for k in range(j + 1, n):
                    c = order[k]
                    if c == u or c == v:
                        continue
                    if not (bits[a] & (1 << c)):
                        continue  # ac not in E
                    need = bits[b] & ~bits[c]
                    if not (need & ((1 << i) - 1) & ~(1 << d)):
                        return False
    return True


def init(graph):
    n = len(graph)
    order = _lexbfs(graph)
    pos = [0] * n
    for i, v in enumerate(order):
        pos[v] = i
    return {
        'ordering': order,
        'n': n,
        'pos': pos,
        'bits': _adj_bits(graph),
    }


def insert_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    pos = state['pos']
    bits = state['bits']
    bits[u] |= 1 << v
    bits[v] |= 1 << u
    if _valid_insert(bits, order, pos, u, v):
        return {
            'ordering': order,
            'n': state['n'],
            'pos': pos,
            'bits': bits,
        }
    new_order = _lexbfs(graph)
    new_pos = [0] * state['n']
    for i, x in enumerate(new_order):
        new_pos[x] = i
    return {
        'ordering': new_order,
        'n': state['n'],
        'pos': new_pos,
        'bits': _adj_bits(graph),
    }


def delete_edge(graph, edge, state):
    u, v = edge
    order = state['ordering']
    pos = state['pos']
    bits = state['bits']
    bits[u] &= ~(1 << v)
    bits[v] &= ~(1 << u)
    if _valid_delete(bits, order, pos, u, v):
        return {
            'ordering': order,
            'n': state['n'],
            'pos': pos,
            'bits': bits,
        }
    new_order = _lexbfs(graph)
    new_pos = [0] * state['n']
    for i, x in enumerate(new_order):
        new_pos[x] = i
    return {
        'ordering': new_order,
        'n': state['n'],
        'pos': new_pos,
        'bits': _adj_bits(graph),
    }
