# Proof strategy for Formal_gen003c01 (dynamic MCS, tight window)

You are proving correctness of the tight-window dynamic MCS candidate. A domain
expert (algorithm reflector) has already analyzed this module. The analysis
shows the two lemmas the previous agent spent hours on are OFF the critical
path. Follow this roadmap.

## State of the module (verified)

Already PROVED (do not redo):
- `prefix_preserved` (base module)
- `neigh_flip_insert` / `neigh_flip_delete`
- `IsMCSNext_of_drop`
- `firstBreak_some`, `firstBreak_none` (lines ~388-465)
- `legal_after_laterPos`, `legal_middle_delete`
- `update_from_prefix` (line ~1090)
- base: `greedySuffix_valid`, `mcsUpdate_preserves_invariant`

REMAINING `sorry` (all truly needed):
1. `insert_break_iff` (line ~1062)  — OFF critical path, see below
2. `deletionBreaks_true_iff` (line ~1076) — OFF critical path, see below
3. `init_valid` (line ~1130) — TRIVIAL, 4 lines
4. `insert_update_valid` (line ~1136) — MAIN theorem
5. `delete_update_valid` (line ~1144) — MAIN theorem

## Key insight: the two biconditionals are NOT needed for the main theorems

- `insert_break_iff` ties the PYTHON arithmetic probe (`d > c ∨ (d = c ∧ v < order[k])`)
  to the LEAN semantic probe (`IsMCSNext`). The Lean model's `firstBreakWindow`
  already uses the SEMANTIC probe directly (checks `IsMCSNext`). So
  `insert_update_valid` never needs `insert_break_iff`. DROP it from the critical path.
- `deletionBreaks_true_iff` ties the arithmetic deletion scan to the semantic
  condition. `delete_update_valid` needs ONLY ONE DIRECTION:
  `deletionBreaks = false → w is a legal MCS pick at step laterPos`, which is a
  clean application of `neigh_flip_delete` + `IsMCSNext_of_drop` (both proved).
  The full `↔` is over-specified. DROP the full biconditional.

## How to assemble the three main theorems (from ALREADY-PROVED lemmas)

### init_valid (trivial)
Mirror base `init_valid`:
```
greedySuffix_valid G [] List.nodup_nil trivial
```
`initOrder H = greedySuffix H []`, so `init_valid` is 4 lines.

### insert_update_valid
Case split on `firstBreakWindow`:
- `none`: every step legal via `prefix_preserved` (steps `≤ earlierPos`) +
  `firstBreak_none` (window `(earlierPos, laterPos]`) + `legal_after_laterPos`
  (steps `> laterPos`) → `ordering_of_steps_legal` + `greedySuffix_full`.
- `some k`: retained prefix `order.take k` is legal via `prefix_preserved` +
  `firstBreak_some` → `update_from_prefix` + `greedySuffix_valid`.

### delete_update_valid
Case split on the (semantic) deletion probe:
- `false`: steps legal via `prefix_preserved` + `legal_middle_delete` +
  (probe false = step `laterPos` legal, by definition of the semantic probe) +
  `legal_after_laterPos` → `ordering_of_steps_legal`.
- `true`: prefix legal via `prefix_preserved` + `legal_middle_delete` →
  `update_from_prefix`.

## Recommended code changes in THIS module

1. Redefine the deletion probe SEMANTICALLY (eliminate the arithmetic scan):
   replace `deletionBreaks` with
   `isFalse (IsMCSNext G' (order.take (laterPos order u v)) (laterVert order u v))`
   and redefine `deleteUpdate` to use it. Then `deletionBreaks_true_iff` is
   ELIMINATED, not half-proved.
2. Do NOT attempt `insert_break_iff` unless everything else is done; it is an
   optional implementation-faithfulness lemma, not a prerequisite.
3. Prove `init_valid` first (trivial), then the two main theorems.

## Constraints
- No `sorry`, no `axiom`, no `admit`, no `unsafe` in the final module.
- `lake build ThesisLean.Formal_gen003c01_eea71821` must succeed with zero sorry
  warnings at the end.
- Work in stages: prove one lemma, build, next. Do NOT write the whole thing at once.