"""Dynamic LexBFS ordering.

Strategy: maintain a valid LexBFS ordering incrementally.

- init: run the standard partition-refinement LexBFS (Habib-McConnell-Paul-Viennot).
- insert_edge(u,v): if the current ordering is still valid (checked via the
  (LB) 4-point property), keep it.  Otherwise recompute.
- delete_edge(u,v): if the current ordering is still valid, keep it.
  Otherwise recompute.

The validity check is O(n^2) using the (LB) property:
  for all positions a < b < c with ac in E and ab not in E,
  there exists d < a with db in E and dc not in E.

This is correct because we always return a valid LexBFS ordering.
The incremental check avoids a full recompute when the ordering is
still valid after the update.
"""


def _lexbfs(graph):
    """Static LexBFS via partition refinement. Returns ordering list."""
    n = len(graph)
    if n == 0:
        return []

    # Build adjacency sets
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if graph[i][j]:
                adj[i].add(j)
                adj[j].add(i)

    # Partition refinement LexBFS
    # P is a list of sets (the current partition), ordered.
    # We use a queue of (vertex, set) pairs for refinement.

    # Start: all vertices in one set
    P = [set(range(n))]
    # Order of sets in P matters; we process them in order.

    # We'll use a list of sets and a queue of (v, S) where S is the set
    # containing v that needs to be split by N(v).

    from collections import deque
    Q = deque()
    # Initially pick vertex 0 (or any) as the first
    # Actually, standard LexBFS: start with all vertices in one bucket.
    # Pick the first vertex (smallest id) from the first bucket.

    # Let's use the standard algorithm:
    # P = [V]  (one bucket)
    # while P is not empty:
    #   take the first bucket S in P
    #   pick v in S (first element)
    #   remove v from S, add v to output
    #   if S is non-empty, split S by N(v): S1 = S ∩ N(v), S2 = S \ N(v)
    #   for each other bucket T in P: split T by N(v)
    #   (the split buckets replace T in P, with S1 before S2)

    # Implementation with list of sets
    P = [set(range(n))]
    order = []

    while P:
        # Take the first bucket
        S = P[0]
        if not S:
            P.pop(0)
            continue
        # Pick the first vertex (smallest id for determinism)
        v = min(S)
        S.remove(v)
        order.append(v)

        # Split S by N(v)
        if S:
            S1 = {x for x in S if x in adj[v]}
            S2 = S - S1
            # Replace S in P[0] with S1, S2 (S1 first)
            new_buckets = []
            if S1:
                new_buckets.append(S1)
            if S2:
                new_buckets.append(S2)
            P[0:1] = new_buckets

        # Split all other buckets by N(v)
        for i in range(1, len(P)):
            T = P[i]
            T1 = {x for x in T if x in adj[v]}
            T2 = T - T1
            new_buckets = []
            if T1:
                new_buckets.append(T1)
            if T2:
                new_buckets.append(T2)
            P[i:i+1] = new_buckets

    return order


def _is_valid_lexbfs(ordering, graph):
    """Check if ordering is a valid LexBFS ordering using the (LB) property.

    (LB): for all positions a < b < c with ac in E and ab not in E,
    there exists d < a with db in E and dc not in E.

    Here a, b, c, d are vertices, and positions refer to their indices
    in the ordering.
    """
    n = len(ordering)
    if n <= 2:
        return True

    # pos[v] = position of v in ordering
    pos = [0] * n
    for i, v in enumerate(ordering):
        pos[v] = i

    # adj as sets for fast lookup
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if graph[i][j]:
                adj[i].add(j)
                adj[j].add(i)

    # For each pair (a, b) with pos[a] < pos[b], check the condition.
    # We need: if there exists c with pos[c] > pos[b] and ac in E and ab not in E,
    # then there must exist d with pos[d] < pos[a] and db in E and dc not in E.

    # To make this efficient, for each (a, b) with ab not in E:
    #   Let C = {c : pos[c] > pos[b], ac in E}
    #   If C is non-empty, we need: exists d < pos[a] with db in E and dc not in E for all c in C?
    #   No: the property says "there exists d < a with db in E and dc not in E"
    #   for the specific c. Wait, let me re-read.

    # (LB): for all a < b < c with ac in E and ab not in E,
    #       there exists d < a with db in E and dc not in E.

    # So for each triple (a, b, c) with pos[a] < pos[b] < pos[c],
    # ac in E, ab not in E:
    #   need exists d with pos[d] < pos[a], db in E, dc not in E.

    # This is O(n^4) naively. Let's optimize.

    # For fixed (a, b) with ab not in E and pos[a] < pos[b]:
    #   Let C = {c : pos[c] > pos[b], c in adj[a]}
    #   If C is empty, no constraint.
    #   Otherwise, for each c in C, we need exists d < pos[a] with d in adj[b] and d not in adj[c].
    #   Equivalently: for each c in C, adj[b] ∩ {d : pos[d] < pos[a]} is not a subset of adj[c].
    #   i.e., there exists d in adj[b] with pos[d] < pos[a] and d not in adj[c].

    # Let D_b = {d in adj[b] : pos[d] < pos[a]}
    # For each c in C: need D_b not subset of adj[c], i.e., D_b \ adj[c] is non-empty.

    # We can precompute for each vertex x, the set of vertices before x in the ordering.
    # Actually, let's just do it directly but carefully.

    # For efficiency, iterate over (a, b) pairs where ab not in E.
    # For each such pair, compute C and check.

    # Precompute: for each vertex, the set of neighbors.
    # For each (a, b) with pos[a] < pos[b] and ab not in E:
    #   C = adj[a] ∩ {c : pos[c] > pos[b]}
    #   if C empty: continue
    #   D = adj[b] ∩ {d : pos[d] < pos[a]}
    #   for c in C:
    #       if D ⊆ adj[c]: return False
    #   (i.e., if for all d in D, d in adj[c], then fail)

    # To check D ⊆ adj[c] quickly: len(D & adj[c]) == len(D)

    # Let's precompute prefix sets: for each position p, the set of vertices at positions < p.
    # Actually, we can just use pos array.

    for a in range(n):
        for b in range(a + 1, n):
            va = ordering[a]
            vb = ordering[b]
            if vb in adj[va]:
                continue  # ab in E, no constraint
            # ab not in E
            # C = {c : pos[c] > b, c in adj[va]}
            C = [c for c in adj[va] if pos[c] > b]
            if not C:
                continue
            # D = {d : pos[d] < a, d in adj[vb]}
            D = [d for d in adj[vb] if pos[d] < a]
            if not D:
                # No d before a adjacent to b, so for any c in C,
                # we need d < a with db in E and dc not in E.
                # But D is empty, so no such d exists. Fail.
                return False
            # For each c in C, check D not subset of adj[c]
            for c in C:
                # Check if D ⊆ adj[c]
                # i.e., all d in D are in adj[c]
                all_in = True
                for d in D:
                    if d not in adj[c]:
                        all_in = False
                        break
                if all_in:
                    return False
    return True


def init(graph):
    n = len(graph)
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def insert_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    # Check if current ordering is still valid
    if _is_valid_lexbfs(ordering, graph):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}


def delete_edge(graph, edge, state):
    u, v = edge
    ordering = state['ordering']
    # Check if current ordering is still valid
    if _is_valid_lexbfs(ordering, graph):
        return state
    # Recompute
    ordering = _lexbfs(graph)
    return {'ordering': ordering}
