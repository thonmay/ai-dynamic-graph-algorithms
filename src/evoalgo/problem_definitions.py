"""Problem definitions: invariants, oracles, and offline algorithms.

Each problem owns:
  - check_invariant(state, graph, root_or_source) -> bool
  - extract_result(state) -> the maintained result (tree, ordering, partition, set)
  - offline_compute(graph, root_or_source) -> the reference result
  - baseline_work(graph) -> int (work for offline recomputation)

The candidate's state contains the maintained result. The verifier calls
the candidate's init/insert_edge/delete_edge, then asks the problem definition
to check the invariant on the current state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import Any

import numpy as np


class ProblemDefinition(ABC):
    """Base class for problem definitions."""

    name: str = "abstract"
    directed: bool = True
    needs_root: bool = True  # BFS, DFS, reachability need a root/source

    @abstractmethod
    def extract_result(self, state: Any) -> Any:
        """Extract the maintained result from candidate state."""
        ...

    @abstractmethod
    def check_invariant(self, state: Any, graph: np.ndarray, root: int | None) -> bool:
        """Check the problem's invariant on the current state and graph."""
        ...

    @abstractmethod
    def offline_compute(self, graph: np.ndarray, root: int | None) -> Any:
        """Compute the reference result from scratch."""
        ...

    @abstractmethod
    def baseline_work(self, graph: np.ndarray) -> int:
        """Estimate work for offline recomputation (vertices + edges scanned)."""
        ...

    @property
    def offline_source(self) -> str:
        """Return standalone source code for the offline algorithm.

        This is exec'd in the sandbox subprocess to time the offline
        baseline alongside the candidate. Must be a self-contained
        function named offline_compute(graph, root) with no `self` refs.
        Subclasses override this to provide the source.
        """
        return ""

    def failing_context(self, state: Any, graph: np.ndarray, root: int | None) -> dict:
        """Return a structured description of the failure for reflection."""
        result = self.extract_result(state)
        expected = self.offline_compute(graph, root)
        return {
            "problem": self.name,
            "result": str(result),
            "expected": str(expected),
            "graph_shape": list(graph.shape),
        }


class DynamicBFS(ProblemDefinition):
    name = "dynamic_bfs"
    directed = True
    needs_root = True

    OFFLINE_SOURCE = '''
def offline_compute(graph, root):
    import collections
    n = graph.shape[0]
    parent = {root: None}
    dist = {root: 0}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u, v] == 1 and v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                queue.append(v)
    return {"parent": parent, "distances": dist}
'''

    @property
    def offline_source(self) -> str:
        return self.OFFLINE_SOURCE

    def extract_result(self, state: Any) -> Any:
        # state should contain 'parent' dict or array
        if isinstance(state, dict):
            return state.get("parent", state.get("tree", state))
        return state

    def check_invariant(self, state: Any, graph: np.ndarray, root: int | None) -> bool:
        if root is None:
            return False
        parent = self._extract_parent(state)
        if parent is None:
            return False
        n = graph.shape[0]

        # (1) Every non-root vertex has exactly one parent, root has none
        for v in range(n):
            if v == root:
                if parent.get(v) is not None:
                    return False
                continue
            p = parent.get(v)
            if p is not None and p != v:
                # Parent must be a neighbor in the graph
                if graph[p, v] != 1:
                    return False

        # (2) Tree spans all vertices reachable from root
        distances = self._bfs_distances(graph, root)
        tree_reachable = self._tree_reachable(parent, root, n)
        for v in range(n):
            if distances.get(v, -1) != -1 and v not in tree_reachable:
                return False
            # Reject spurious parents for unreachable vertices
            if distances.get(v, -1) == -1 and parent.get(v) is not None:
                return False

        # (3) Distance property: delta(parent) = delta(v) - 1
        for v in range(n):
            if v == root or v not in tree_reachable:
                continue
            p = parent.get(v)
            if p is None:
                return False
            if distances.get(v, -1) != distances.get(p, -1) + 1:
                return False

        return True

    def offline_compute(self, graph: np.ndarray, root: int | None) -> dict:
        return self._bfs_tree(graph, root)

    def baseline_work(self, graph: np.ndarray) -> int:
        n = graph.shape[0]
        return n + int(graph.sum())

    def _extract_parent(self, state: Any) -> dict[int, int | None] | None:
        if isinstance(state, dict):
            p = state.get("parent")
            if isinstance(p, dict):
                return {int(k): v for k, v in p.items()}
            if isinstance(p, (list, tuple)):
                return {i: v for i, v in enumerate(p)}
            if isinstance(p, np.ndarray):
                return {i: int(p[i]) for i in range(len(p))}
        return None

    def _bfs_distances(self, graph: np.ndarray, root: int) -> dict[int, int]:
        n = graph.shape[0]
        dist = {root: 0}
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v in range(n):
                if graph[u, v] == 1 and v not in dist:
                    dist[v] = dist[u] + 1
                    queue.append(v)
        return dist

    def _bfs_tree(self, graph: np.ndarray, root: int | None) -> dict:
        n = graph.shape[0]
        parent: dict[int, int | None] = {root: None}
        dist = {root: 0}
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v in range(n):
                if graph[u, v] == 1 and v not in dist:
                    dist[v] = dist[u] + 1
                    parent[v] = u
                    queue.append(v)
        return {"parent": parent, "distances": dist}

    def _tree_reachable(self, parent: dict, root: int, n: int) -> set[int]:
        reachable = {root}
        # Build children map
        children: dict[int, list[int]] = {}
        for v, p in parent.items():
            if p is not None and p != v:
                children.setdefault(p, []).append(v)
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v in children.get(u, []):
                if v not in reachable:
                    reachable.add(v)
                    queue.append(v)
        return reachable


class DynamicDFS(ProblemDefinition):
    name = "dynamic_dfs"
    directed = True
    needs_root = True

    OFFLINE_SOURCE = '''
def offline_compute(graph, root):
    n = graph.shape[0]
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
            if graph[u, v] == 1 and v not in visited:
                parent[v] = u
                dfs(v)
        finish[u] = timer[0]
        timer[0] += 1

    if root is not None:
        dfs(root)
    return {"parent": parent, "discover": discover, "finish": finish}
'''

    @property
    def offline_source(self) -> str:
        return self.OFFLINE_SOURCE

    def extract_result(self, state: Any) -> Any:
        if isinstance(state, dict):
            return {
                "parent": state.get("parent"),
                "discover": state.get("discover", state.get("disc")),
                "finish": state.get("finish"),
            }
        return state

    def check_invariant(self, state: Any, graph: np.ndarray, root: int | None) -> bool:
        if root is None:
            return False
        if not isinstance(state, dict):
            return False
        parent = state.get("parent")
        discover = state.get("discover", state.get("disc"))
        finish = state.get("finish")
        if parent is None or discover is None:
            return False

        # Normalize to dicts
        parent = self._normalize_dict(parent, graph.shape[0])
        discover = self._normalize_dict(discover, graph.shape[0])
        finish = self._normalize_dict(finish, graph.shape[0]) if finish else None

        # Verify DFS forest certificate: parent pointers + discovery/finish times
        # are consistent with a DFS of the current graph per Yang et al.
        return self._verify_dfs_certificate(graph, root, parent, discover, finish)

    def offline_compute(self, graph: np.ndarray, root: int | None) -> dict:
        n = graph.shape[0]
        parent: dict[int, int | None] = {i: None for i in range(n)}
        discover: dict[int, int] = {}
        finish: dict[int, int] = {}
        visited = set()
        timer = [0]

        def dfs(u: int):
            visited.add(u)
            discover[u] = timer[0]
            timer[0] += 1
            for v in range(n):
                if graph[u, v] == 1 and v not in visited:
                    parent[v] = u
                    dfs(v)
            finish[u] = timer[0]
            timer[0] += 1

        if root is not None:
            dfs(root)
        return {"parent": parent, "discover": discover, "finish": finish}

    def baseline_work(self, graph: np.ndarray) -> int:
        n = graph.shape[0]
        return n + int(graph.sum())

    def _normalize_dict(self, data: Any, n: int) -> dict[int, Any]:
        if isinstance(data, dict):
            return {int(k): v for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return {i: data[i] for i in range(len(data))}
        if isinstance(data, np.ndarray):
            return {i: int(data[i]) for i in range(len(data))}
        return {}

    def _verify_dfs_certificate(
        self,
        graph: np.ndarray,
        root: int,
        parent: dict[int, int | None],
        discover: dict[int, int],
        finish: dict[int, int] | None,
    ) -> bool:
        n = graph.shape[0]

        # Root must have no parent and must be discovered
        if parent.get(root) is not None:
            return False
        if root not in discover:
            return False

        # Every vertex reachable from root must be in the forest
        reachable = self._reachable_vertices(graph, root)
        for v in reachable:
            if v not in discover:
                return False

        # Parent pointers: for each non-root v in forest, parent[v] must be
        # a neighbor (u -> v edge exists) and u must be discovered before v
        for v in reachable:
            if v == root:
                continue
            p = parent.get(v)
            if p is None:
                return False
            if graph[p, v] != 1:
                return False
            if discover.get(p, -1) >= discover.get(v, -1):
                return False

        # If finish times provided, verify interval nesting:
        # for edge u->v where both are in forest, either:
        #   v is a descendant of u (discover[u] < discover[v] < finish[v] < finish[u])
        #   or u is a descendant of v
        #   or they are in separate branches (intervals don't nest)
        # The key check: no forward-cross edge.
        # For non-tree edge u->v where discover[u] < discover[v]:
        #   v must be a descendant of u (i.e., finish[v] < finish[u] if finish exists)
        if finish:
            for u in reachable:
                for v in reachable:
                    if u != v and graph[u, v] == 1:
                        du, dv = discover.get(u, -1), discover.get(v, -1)
                        fu, fv = finish.get(u, -1), finish.get(v, -1)
                        if du < dv:
                            # u discovered before v. If v is not a descendant of u,
                            # this is a forward-cross edge -> invalid DFS forest.
                            # v is a descendant of u iff discover[u] < discover[v] < finish[v] < finish[u]
                            if not (du < dv < fv < fu):
                                return False
        else:
            # Without finish times, do a weaker check: verify the forest could
            # be produced by some DFS by replaying with the same neighbor order
            return self._replay_dfs(graph, root, parent, discover)

        return True

    def _reachable_vertices(self, graph: np.ndarray, root: int) -> set[int]:
        n = graph.shape[0]
        visited = set()
        stack = [root]
        while stack:
            u = stack.pop()
            if u in visited:
                continue
            visited.add(u)
            for v in range(n):
                if graph[u, v] == 1 and v not in visited:
                    stack.append(v)
        return visited

    def _replay_dfs(
        self,
        graph: np.ndarray,
        root: int,
        parent: dict[int, int | None],
        discover: dict[int, int],
    ) -> bool:
        """Weak DFS certificate check without finish times:
        verify that a DFS following the tree structure produces the same
        discovery order."""
        n = graph.shape[0]
        # Build children from parent
        children: dict[int, list[int]] = {}
        for v, p in parent.items():
            if p is not None and p != v:
                children.setdefault(p, []).append(v)
        # Sort children by discovery time
        for u in children:
            children[u].sort(key=lambda x: discover.get(x, 0))

        visited = set()
        order = []
        timer = [0]

        def dfs(u: int):
            visited.add(u)
            if discover.get(u) != timer[0]:
                return False
            timer[0] += 1
            order.append(u)
            for v in children.get(u, []):
                if v not in visited:
                    if not dfs(v):
                        return False
            return True

        return dfs(root)


class DynamicMCS(ProblemDefinition):
    """Maximal Cardinality Search ordering (undirected)."""

    name = "dynamic_mcs"
    directed = False
    needs_root = False

    OFFLINE_SOURCE = '''
def offline_compute(graph, root):
    n = graph.shape[0]
    chosen = set()
    cardinality = {v: 0 for v in range(n)}
    ordering = []

    for _ in range(n):
        unchosen = [u for u in range(n) if u not in chosen]
        if not unchosen:
            break
        max_card = max(cardinality[u] for u in unchosen)
        candidates = [u for u in unchosen if cardinality[u] == max_card]
        v = min(candidates)
        ordering.append(v)
        chosen.add(v)
        for u in range(n):
            if graph[v, u] == 1 and u not in chosen:
                cardinality[u] += 1

    return ordering
'''

    @property
    def offline_source(self) -> str:
        return self.OFFLINE_SOURCE

    def extract_result(self, state: Any) -> Any:
        if isinstance(state, dict):
            return state.get("ordering", state.get("order", state))
        return state

    def check_invariant(self, state: Any, graph: np.ndarray, root: int | None) -> bool:
        ordering = self._extract_ordering(state)
        if ordering is None:
            return False
        n = graph.shape[0]
        if len(ordering) != n:
            return False
        if set(ordering) != set(range(n)):
            return False

        # MCS property: each vertex is chosen when its cardinality
        # (number of already-chosen neighbors) is maximal among unchosen.
        chosen = set()
        cardinality = {v: 0 for v in range(n)}

        for v in ordering:
            # Check that v has maximum cardinality among unchosen
            unchosen = [u for u in range(n) if u not in chosen]
            if not unchosen:
                break
            max_card = max(cardinality[u] for u in unchosen)
            if cardinality[v] != max_card:
                return False
            chosen.add(v)
            # Update cardinalities for neighbors
            for u in range(n):
                if graph[v, u] == 1 and u not in chosen:
                    cardinality[u] += 1

        return True

    def offline_compute(self, graph: np.ndarray, root: int | None) -> list[int]:
        n = graph.shape[0]
        chosen = set()
        cardinality = {v: 0 for v in range(n)}
        ordering = []

        for _ in range(n):
            unchosen = [u for u in range(n) if u not in chosen]
            if not unchosen:
                break
            max_card = max(cardinality[u] for u in unchosen)
            # Tie-break: lowest vertex id (deterministic)
            candidates = [u for u in unchosen if cardinality[u] == max_card]
            v = min(candidates)
            ordering.append(v)
            chosen.add(v)
            for u in range(n):
                if graph[v, u] == 1 and u not in chosen:
                    cardinality[u] += 1

        return ordering

    def baseline_work(self, graph: np.ndarray) -> int:
        n = graph.shape[0]
        return n * n  # O(n^2) for MCS

    def _extract_ordering(self, state: Any) -> list[int] | None:
        if isinstance(state, dict):
            order = state.get("ordering", state.get("order"))
            if order is not None:
                return [int(x) for x in order]
        if isinstance(state, (list, tuple)):
            return [int(x) for x in state]
        return None


class DynamicSCC(ProblemDefinition):
    """Strongly Connected Components partition (directed)."""

    name = "dynamic_scc"
    directed = True
    needs_root = False

    OFFLINE_SOURCE = '''
def offline_compute(graph, root):
    n = graph.shape[0]
    index_counter = [0]
    stack = []
    lowlink = [0] * n
    index = [0] * n
    on_stack = [False] * n
    visited = [False] * n
    result = []

    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True
        visited[v] = True

        for w in range(n):
            if graph[v, w] == 1:
                if not visited[w]:
                    strongconnect(w)
                    lowlink[v] = min(lowlink[v], lowlink[w])
                elif on_stack[w]:
                    lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                comp.append(w)
                if w == v:
                    break
            result.append(comp)

    for v in range(n):
        if not visited[v]:
            strongconnect(v)

    return result
'''

    @property
    def offline_source(self) -> str:
        return self.OFFLINE_SOURCE

    def extract_result(self, state: Any) -> Any:
        if isinstance(state, dict):
            return state.get("components", state.get("sccs", state))
        return state

    def check_invariant(self, state: Any, graph: np.ndarray, root: int | None) -> bool:
        components = self._extract_components(state)
        if components is None:
            return False
        n = graph.shape[0]

        # (2) Disjoint and (3) cover all vertices
        all_vertices: set[int] = set()
        for comp in components:
            for v in comp:
                if v in all_vertices:
                    return False  # not disjoint
                all_vertices.add(v)
        if all_vertices != set(range(n)):
            return False

        # (1) Within each Ci, every vertex reaches every other via edges inside Ci
        for comp in components:
            comp_set = set(comp)
            for u in comp:
                for v in comp:
                    if u != v and not self._reachable_within(graph, u, v, comp_set):
                        return False

        # (4) Maximality: no proper superset of Ci is internally mutually reachable
        # Check that merging any two components is impossible
        for i, ci in enumerate(components):
            for j, cj in enumerate(components):
                if i >= j:
                    continue
                merged = set(ci) | set(cj)
                all_reach = True
                for u in merged:
                    for v in merged:
                        if u != v and not self._reachable_within(graph, u, v, merged):
                            all_reach = False
                            break
                    if not all_reach:
                        break
                if all_reach:
                    return False  # should have been one component

        return True

    def offline_compute(self, graph: np.ndarray, root: int | None) -> list[list[int]]:
        return self._tarjan_scc(graph)

    def baseline_work(self, graph: np.ndarray) -> int:
        n = graph.shape[0]
        return n + int(graph.sum())

    def _extract_components(self, state: Any) -> list[set[int]] | None:
        if isinstance(state, dict):
            comps = state.get("components", state.get("sccs"))
            if comps is None:
                return None
            state = comps
        if isinstance(state, (list, tuple)):
            result = []
            for comp in state:
                if isinstance(comp, (set, frozenset)):
                    result.append(set(int(x) for x in comp))
                elif isinstance(comp, (list, tuple)):
                    result.append(set(int(x) for x in comp))
                else:
                    result.append({int(comp)})
            return result
        return None

    def _reachable_within(self, graph: np.ndarray, u: int, v: int, allowed: set[int]) -> bool:
        n = graph.shape[0]
        visited = {u}
        stack = [u]
        while stack:
            x = stack.pop()
            if x == v:
                return True
            for y in range(n):
                if graph[x, y] == 1 and y in allowed and y not in visited:
                    visited.add(y)
                    stack.append(y)
        return v in visited

    def _tarjan_scc(self, graph: np.ndarray) -> list[list[int]]:
        n = graph.shape[0]
        index_counter = [0]
        stack: list[int] = []
        lowlink = [0] * n
        index = [0] * n
        on_stack = [False] * n
        visited = [False] * n
        result: list[list[int]] = []

        def strongconnect(v: int):
            index[v] = index_counter[0]
            lowlink[v] = index_counter[0]
            index_counter[0] += 1
            stack.append(v)
            on_stack[v] = True
            visited[v] = True

            for w in range(n):
                if graph[v, w] == 1:
                    if not visited[w]:
                        strongconnect(w)
                        lowlink[v] = min(lowlink[v], lowlink[w])
                    elif on_stack[w]:
                        lowlink[v] = min(lowlink[v], index[w])

            if lowlink[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    comp.append(w)
                    if w == v:
                        break
                result.append(comp)

        for v in range(n):
            if not visited[v]:
                strongconnect(v)

        return result


class Reachability(ProblemDefinition):
    """Reachability set from a fixed source (directed)."""

    name = "reachability"
    directed = True
    needs_root = True

    OFFLINE_SOURCE = '''
def offline_compute(graph, root):
    import collections
    n = graph.shape[0]
    visited = {root}
    queue = collections.deque([root])
    while queue:
        u = queue.popleft()
        for v in range(n):
            if graph[u, v] == 1 and v not in visited:
                visited.add(v)
                queue.append(v)
    return visited
'''

    @property
    def offline_source(self) -> str:
        return self.OFFLINE_SOURCE

    def extract_result(self, state: Any) -> Any:
        if isinstance(state, dict):
            return state.get("reachable", state.get("set", state))
        return state

    def check_invariant(self, state: Any, graph: np.ndarray, root: int | None) -> bool:
        if root is None:
            return False
        maintained = self._extract_set(state)
        if maintained is None:
            return False
        true_reachable = self._bfs_reachable(graph, root)
        return maintained == true_reachable

    def offline_compute(self, graph: np.ndarray, root: int | None) -> set[int]:
        return self._bfs_reachable(graph, root)

    def baseline_work(self, graph: np.ndarray) -> int:
        n = graph.shape[0]
        return n + int(graph.sum())

    def _extract_set(self, state: Any) -> set[int] | None:
        if isinstance(state, dict):
            s = state.get("reachable", state.get("set"))
            if s is None:
                return None
            state = s
        if isinstance(state, (set, frozenset)):
            return set(int(x) for x in state)
        if isinstance(state, (list, tuple)):
            return set(int(x) for x in state)
        if isinstance(state, np.ndarray):
            return set(int(x) for x in state)
        return None

    def _bfs_reachable(self, graph: np.ndarray, root: int) -> set[int]:
        n = graph.shape[0]
        visited = {root}
        queue = deque([root])
        while queue:
            u = queue.popleft()
            for v in range(n):
                if graph[u, v] == 1 and v not in visited:
                    visited.add(v)
                    queue.append(v)
        return visited


# Registry
PROBLEMS: dict[str, type[ProblemDefinition]] = {
    "dynamic_bfs": DynamicBFS,
    "dynamic_dfs": DynamicDFS,
    "dynamic_mcs": DynamicMCS,
    "dynamic_scc": DynamicSCC,
    "reachability": Reachability,
}


def get_problem(name: str) -> ProblemDefinition:
    cls = PROBLEMS.get(name)
    if cls is None:
        raise ValueError(f"Unknown problem: {name}. Available: {list(PROBLEMS.keys())}")
    return cls()
