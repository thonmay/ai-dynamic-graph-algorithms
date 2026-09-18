# AI-Assisted Discovery of Dynamic Graph Algorithms via Evolutionary Code Repair

Master's thesis project at Eotvos Lorand University, Faculty of Informatics.

A research platform combining LLM-driven evolutionary code repair with exhaustive
isomorphism-aware verification to assist algorithm designers in developing correct
and efficient dynamic graph algorithms on directed graphs.

## Thesis Documents

- [`docs/topic-proposal.txt`](docs/topic-proposal.txt) - Topic proposal and problem statement
- [`docs/planning-spec-short.tex`](docs/planning-spec-short.tex) - Software Requirements Specification (LaTeX source)
- [`docs/design.tex`](docs/design.tex) - Software Design Document (LaTeX source)
- [`docs/design.pdf`](docs/design.pdf) - Compiled Design Document

## Project Overview

The system runs an evolutionary loop in which candidate dynamic graph algorithms
(generated and repaired by cooperative AI agents) are tested exhaustively against
all non-isomorphic digraphs (enumerated via nauty's `geng` + `directg`) and scored
on correctness and efficiency relative to full offline recomputation.

Supported problem tiers:

- Calibration: dynamic BFS, dynamic DFS (known solutions exist)
- Harder: dynamic SCC, reachability
- Open: dynamic Lexicographic BFS (genuine discovery target)

Core principles:

- Correctness by invariant, not by reference equality (dynamic outputs are not unique)
- Verification engine is trusted infrastructure, never exposed to agents
- Sequence-based testing of interleaved edge insertions and deletions
- Exhaustive isomorphism-aware coverage up to n <= 5, random sampling beyond
- LLM-agnostic provider abstraction, CLI-driven, JSON filesystem persistence

## Status

Design phase. Code implementation is the next phase.