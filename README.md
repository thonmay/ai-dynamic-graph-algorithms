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

## Lean Formalization

The dynamic MCS candidate `gen001_c01` is formalized and proved correct in Lean 4 +
mathlib under [`lean/`](lean/). The headline theorem `mcsUpdate_preserves_invariant`
states that the candidate's update preserves a valid MCS ordering under every single
edge flip; `init_valid`, `insert_edge_valid` and `delete_edge_valid` follow.

Verify the proof is honest (builds, no `sorry`, standard axioms only):

```bash
cd lean
lake build ThesisLean.Formal_gen001c01_3939115c   # must end "Build completed successfully"
lake env lean AxiomAudit.lean                      # each theorem: [propext, Classical.choice, Quot.sound]
lake env leanchecker ThesisLean.Formal_gen001c01_3939115c   # kernel replay, exit 0
```

Toolchain: `leanprover/lean4:v4.34.0`, mathlib `v4.34.0` (see `lean/lean-toolchain`).

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