# Crisp proof variants

Three alternative Lean formalizations of the dynamic MCS correctness theorem,
produced by a parallel three-strategy experiment. They live here (outside the
`ThesisLean.**` lib glob) on purpose: they are NOT part of `lake build` and are
verified standalone with `lake env lean <file>` from the `lean/` project root.

| File | Strategy | Lines | Tradeoff |
|------|----------|-------|----------|
| `crisp_H1_hypothesis_split.lean` | State prefix-preservation as a named hypothesis, prove only the greedy-suffix step. Imports the full proof module. | 82 | Shortest; the hard half (prefix-preservation) is assumed, proved in the main module. |
| `crisp_H2_generic_greedy.lean` | Prove one abstract greedy-builder theorem over a generic score, instantiate to MCS. Self-contained. | 391 | Reuses across the thesis's other greedy problems (BFS/SCC); MCS part stays ~127 lines. |
| `crisp_H3_reshaped.lean` | Same theorem, no hypothesis; reshape `neigh` and the loop so the invariant is near-syntactic. Self-contained. | 346 | Honest headline: full strength, 28% shorter than the 480-line main proof. |

All three: `lake env lean` clean, no `sorry`/`axiom`/`unsafe`, axioms =
`[propext, Classical.choice, Quot.sound]`. H3 is the recommended elegant
artifact for the thesis body; the 480-line `ThesisLean/Formal_gen001c01_3939115c.lean`
remains the canonical full-evidence proof.
