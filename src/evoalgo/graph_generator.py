"""Graph generation for the bounded test universe.

For n <= n_max: enumerate all labeled simple loop-free digraphs on n vertices.
  (Nauty would give non-isomorphic graphs, but nauty is not available here.
  Labeled enumeration is actually more thorough for correctness testing since
  it tests every possible edge configuration. The tradeoff is count: n=5
  directed has 2^20 = 1M graphs, so we cap exhaustive at n=4 and use seeded
  random sampling for n=5 and beyond.)

For n > n_max: seeded random graphs from a stated distribution.
"""

from __future__ import annotations

import itertools
import random
from typing import Iterator

import numpy as np


def enumerate_digraphs(n: int) -> Iterator[np.ndarray]:
    """Yield all labeled loop-free digraphs on n vertices as adjacency matrices.

    For directed graphs: each off-diagonal entry is 0 or 1 independently.
    Count: 2^(n*(n-1)).
    """
    pairs = n * (n - 1)  # directed: n*(n-1) possible edges
    for bits in range(2**pairs):
        mat = np.zeros((n, n), dtype=int)
        idx = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    mat[i, j] = (bits >> idx) & 1
                    idx += 1
        yield mat


def enumerate_undirected_graphs(n: int) -> Iterator[np.ndarray]:
    """Yield all labeled loop-free undirected graphs on n vertices.

    For undirected: only upper triangle entries are free.
    Count: 2^(n*(n-1)/2).
    """
    pairs = n * (n - 1) // 2
    for bits in range(2**pairs):
        mat = np.zeros((n, n), dtype=int)
        idx = 0
        for i in range(n):
            for j in range(i + 1, n):
                val = (bits >> idx) & 1
                mat[i, j] = val
                mat[j, i] = val
                idx += 1
        yield mat


def sample_digraphs(n: int, count: int, seed: int, p: float = 0.3) -> list[np.ndarray]:
    """Sample random loop-free digraphs with edge probability p."""
    rng = random.Random(seed)
    graphs = []
    for _ in range(count):
        mat = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(n):
                if i != j and rng.random() < p:
                    mat[i, j] = 1
        graphs.append(mat)
    return graphs


def sample_undirected_graphs(n: int, count: int, seed: int, p: float = 0.3) -> list[np.ndarray]:
    """Sample random loop-free undirected graphs with edge probability p."""
    rng = random.Random(seed)
    graphs = []
    for _ in range(count):
        mat = np.zeros((n, n), dtype=int)
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    mat[i, j] = 1
                    mat[j, i] = 1
        graphs.append(mat)
    return graphs


def generate_test_graphs(
    n_max: int,
    n_random: int,
    seed: int,
    directed: bool,
    exhaustive_cap: int = 4,
) -> list[tuple[int, np.ndarray]]:
    """Generate the bounded test universe of base graphs.

    Returns list of (n, adjacency_matrix) pairs.

    For n <= exhaustive_cap: all labeled graphs (exhaustive).
    For exhaustive_cap < n <= n_max: seeded random samples.
    For n > n_max: n_random seeded random samples per size up to n_max.
    """
    result: list[tuple[int, np.ndarray]] = []
    rng_seed = seed

    for n in range(2, n_max + 1):
        if directed:
            if n <= exhaustive_cap:
                for g in enumerate_digraphs(n):
                    result.append((n, g))
            else:
                # Sample for larger n
                count = min(n_random, 200)
                for g in sample_digraphs(n, count, rng_seed):
                    result.append((n, g))
                rng_seed += 1
        else:
            if n <= exhaustive_cap:
                for g in enumerate_undirected_graphs(n):
                    result.append((n, g))
            else:
                count = min(n_random, 200)
                for g in sample_undirected_graphs(n, count, rng_seed):
                    result.append((n, g))
                rng_seed += 1

    return result


def generate_operation_sequences(
    n: int,
    graph: np.ndarray,
    seq_len_max: int,
    seq_count: int,
    seed: int,
    directed: bool = True,
) -> list[list[tuple[str, tuple[int, int]]]]:
    """Generate bounded sequences of edge insertions and deletions.

    Each operation is ('insert', (u, v)) or ('delete', (u, v)).
    Operations are legal: insert only if edge absent, delete only if present.
    """
    rng = random.Random(seed)
    sequences = []

    for s in range(seq_count):
        seq = []
        current = graph.copy()
        for _ in range(seq_len_max):
            # Pick a random non-diagonal cell
            u = rng.randint(0, n - 1)
            v = rng.randint(0, n - 1)
            while v == u:
                v = rng.randint(0, n - 1)

            if current[u, v] == 0:
                current[u, v] = 1
                if not directed:
                    current[v, u] = 1
                seq.append(("insert", (u, v)))
            else:
                current[u, v] = 0
                if not directed:
                    current[v, u] = 0
                seq.append(("delete", (u, v)))
        sequences.append(seq)

    return sequences
