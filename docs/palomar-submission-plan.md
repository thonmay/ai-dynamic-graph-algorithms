# Palomar Submission: Dynamic MCS Ordering Maintenance — Formalization Plan

Status: planning. Owner: Md Thoriqul Islam Thonmay (supervisor Gregory Morse, co-author TBD).
Repo: `thonmay/thesis-lean` (master). Lean 4.34.0 + Mathlib. CI green.

## Goal

Register a Lean-verified dynamic MCS ordering maintenance algorithm with the
[Palomar Registry](https://palomar-registry.org), following the supervisor's
framework: separate incremental and decremental correctness + complexity
headline theorems, with the bridge theorem and invariant theory as the prior
theory they build on. All proofs machine-checked (lake build + leanchecker),
zero `sorry`/axiom in the Solution.

## Supervisor's requirements (verbatim intent)

- "Only the main headline results" go in the Challenge/formatted statement.
  Dependencies are fine as dependencies, not headline-worthy.
- Headline theorems: "Algorithm MCSIncremental maintains an MCS order" and
  "Algorithm MCSIncremental performs in O(m+n) time and space" — likewise for
  the decremental: 4 top-level theorems total.
- "Incremental/decremental are still separate algorithms; fully dynamic
  refers to the compatible data structure."
- Top-level results from the existing 36 theorems "absolutely can be included
  especially if they are top level results they should be."
- Proving time/space complexity in Lean is "unusual and extremely rigorous";
  explicitly a headline item.
- "Your agent will create .github/workflow yamls and a comparator.json,
  formalization file, etc."

## Current state (verified in source)

### Abstract spec (`ThesisLean/Formal_gen001c01_3939115c.lean`)
- `Vert n = Fin n`, `UGraph n` (adj, symm, loopless), `neigh`, `IsMCSNext`,
  `IsMCSOrdering`, `ValidMCSState`, `FlipOf`, `greedySuffix`.
- **Already proved (abstract dynamic correctness):**
  `mcsUpdate_preserves_invariant`, `insert_edge_valid`, `delete_edge_valid`,
  `init_valid`, `exists_IsMCSNext`.

### Candidate algorithm (`ThesisLean/Formal_gen003c01_eea71821.lean`, 36 theorems)
- `initOrder`, `insertUpdate` (probe window `[pu+1, pv]`, conditional regreedy),
  `deleteUpdate` (probe at `pv`, conditional regreedy).
- **Already proved (the dynamic correctness headlines):**
  `insert_update_valid`, `delete_update_valid`, `init_valid`.
- Supporting: firstBreak window lemmas, flip lemmas, legal_middle_delete,
  greedySuffix_full, ordering_of_steps_legal, update_from_prefix, etc.
  (dependencies, not headlines).

### Executable model (`ThesisLean/Exec.lean`)
- Concrete `Adj n = List (List Bool)`, `getAdj`, `cardC`, `bestPick`, `mcsStep`,
  `mcsOrder` (full recomputation via foldl), `setEdge`/`insertEdge`/`deleteEdge`,
  `toUGraph`.
- `#eval` demos work.

### Bridge plumbing (all verified, 0 sorries)
- `BridgeSteps.lean`: R1-R4, `bestPick_lex` (max-card, min-id).
- `CardBridge.lean`: `cardC_eq_neigh`.
- `McsInvariant.lean`: `McListInv`, `foldl_mcsStep_listInv`,
  `bestPick_IsMCSNext`, `mcsStep_terminal_rem_empty`.
- `BridgePartsA/B/C.lean` + `BridgeAssembly.lean`:
  `mcsOrder_eq_greedySuffix` (per-state correctness: executable ordering =
  abstract `IsMCSOrdering`).

### CI
- `.github/workflows/lean_action_ci.yml`: green. Warning: Node 20
  deprecation — `actions/checkout@v5` ok, but `actions/cache/*@v4`
  (pulled transitively by lean-action) target Node 20. Fix to v5.

## The 4 headline theorems (final target)

1. **Incremental correctness** — after an edge *insertion*, the maintained
   MCS ordering stays valid.
   - Abstract: `insert_edge_valid` / `insert_update_valid` (DONE).
   - Executable: dynamic bridge — `Exec.insertEdge` + incremental update
     produces a valid ordering (TODO, Step 5).
2. **Incremental complexity** — insertion probe `O(k)` (`k = pv - pu`),
   conditional regreedy `O(n + m_suffix(k0))`, worst case `O(n + m)` per
   update; space `O(n + m)`. (TODO, Step 3.)
3. **Decremental correctness** — after an edge *deletion*, the maintained
   MCS ordering stays valid.
   - Abstract: `delete_edge_valid` / `delete_update_valid` (DONE).
   - Executable: dynamic bridge — `Exec.deleteEdge` + decremental update
     produces a valid ordering (TODO, Step 5).
4. **Decremental complexity** — deletion probe `O(n)`, conditional regreedy
   `O(n + m_suffix(pv))`, worst case `O(n + m)` per update; space
   `O(n + m)`. (TODO, Step 4.)

Prior theory (dependencies, already proved): bridge theorem
`mcsOrder_eq_greedySuffix`, `bestPick_lex`, `cardC_eq_neigh`, McsInvariant,
plus the supporting 30-ish lemmas of `Formal_gen003c01`.

## Scope decision (recommendation, supervisor to confirm shape)

Single fully-dynamic algorithm (one code path, probe + conditional suffix
regreedy). Present as TWO theorem pairs (incremental/decremental correctness +
complexity) per supervisor's explicit guidance, sharing the same data
structure. Headline variant: the pure-probe algorithm (gen003_c01 — clean
`O(k)`/`O(n)` probe, no rebuild). The adopted gen003_c02 periodic rebuild
(REBUILD_PERIOD=64) is documented in formalization.yaml as a practical
extension, not a headline theorem (its amortized `O((n+m)/64)` term would
muddy the clean statement).

## New Lean work (the gap)

- Step 3: complexity model + incremental complexity theorem.
- Step 4: decremental complexity theorem.
- Step 5: executable dynamic bridge — prove the executable update functions
  (`Exec.insertEdge`/`Exec.deleteEdge` + probe/regreedy as a stateful updater)
  match the abstract `insertUpdate`/`deleteUpdate`; or, more precisely, that
  the executable maintains a valid MCS ordering across a flip sequence.

Complexity formalization approach (to be refined in Step 3):
- Define a cost/count model on the executable structures: probe steps = window
  length scanned; regreedy steps = prefix mask build `O(k0)` + popcounts
  `O(n)` + suffix edge touches `O(m_suffix)`.
- State asymptotic bounds as explicit Big-O (with a domestic `O` definition or
  explicit witness-based `∃ c, ∀ ..., cost ≤ c * f` form — mathlib has
  asymptotics but a self-contained witness bound is more robust for a
  Challenge/Solution comparator).
- Space: the state is a fixed set of lists/bitmasks, `O(n + m)`; a simple
  cardinality bound on the structures.

## Palomar packaging (final deliverable)

Root of `thonmay/thesis-lean`:
- `Challenge.lean` — independent statement, `sorry` proofs, imports ONLY
  Mathlib (and Lean core). Lists the headline declarations (4 theorems +
  bridge theorem + `init_valid`). Target <300 lines, <32 KiB. A mathematician
  should be able to read and audit the statements.
- `Solution.lean` — proved versions, same declaration names/types, imports
  Challenge + the project modules. Zero `sorry`/`sorryAx`/`Lean.ofReduceBool`.
- `comparator.json` — names every compared declaration (the headline set).
- `formalization.yaml` — project metadata, authors, license
  (Apache-2.0), arXiv cs.DS + math.CO, MSC 05C85 + 68Q25 + 68W40 (to verify
  against MSC2020), automation (AI-assisted with manual review; document
  lean-prover agent usage per ELTE AI policy), review status, narrative.
- `lakefile.toml` + `lake-manifest.json` + `lean-toolchain`: present.
- CI: bump the transitive `actions/cache@v5` (fix Node 20 warning), keep
  leanchecker gate.

## Submission flow (agent protocol, no browser)

1. Commit/push the full snapshot; record full 40-char SHA.
2. `POST https://submit.palomar-registry.org/api/submit` with
   `{"repository": "thonmay/thesis-lean", "commit": <SHA>,
     "comparator_config_path": "comparator.json",
     "authorization_relationship": "maintainer"}`.
3. Create tag `palomar-verify-<challenge>` at the commit (gh api).
4. Create secret gist containing the challenge (gh api).
5. `POST /api/verify` with pending_secret + gist_id → access_token.
6. Delete tag + gist.
7. Monitor `GET /api/submission` → review `GET /api/review`.
8. Register `POST /register` ONLY after showing the user the review and
   getting explicit consent.
9. Add supervisor as co-author via a later version of the same entry (Palomar
   supports versioned entries; `existing_id` links them).

## Team/ownership

- Author: Md Thoriqul Islam Thonmay (submitter, maintainer relationship).
- Co-author to add later: Gregory Morse (as new version).
- AI disclosure: formalization AI-assisted (lean-prover agent swarm), proofs
  manually reviewed and independently re-checked with leanchecker; document in
  formalization.yaml per ELTE AI usage policy.

## Risks / open items

- Complexity theorems are the largest new Lean work; supervisor flagged them
  as the rigorous, unusual part. Mitigate with the narrow-slice swarm pattern
  that worked for the bridge.
- Challenge.lean must import only Mathlib/core: our abstract spec modules
  (`Formal_gen001c01`) import only Mathlib, so the Challenge can restate the
  abstract headlines directly; if the executable-side statements are needed in
  the Challenge, they must avoid importing our Exec (which is fine — it only
  imports Mathlib + Formal_gen001c01, both Mathlib-only).
- Comparator compares same-name same-type declarations: the Challenge and
  Solution must use identical signatures; the Solution can be a thin
  `by exact <proved theorem>` wrapper or re-export.
- Verify MSC codes + arXiv categories against the actual classification
  taxonomy before submission.
- The per-flip executable dynamic bridge (Step 5) may be split into slices
  (A: Exec update state machine, B: abstract equivalence, C: assembly) using
  the parallel swarm that succeeded for the static bridge.

## Steps (implementation order)

1. Clean up scratch/bak files in ThesisLean/.
2. Classify the 36 theorems: headline vs dependency (for comparator +
   formalization.yaml narrative).
3. Formalize incremental complexity theorem (+ cost model).
4. Formalize decremental complexity theorem.
5. Formalize executable dynamic bridge (updates preserve validity).
6. Create Challenge.lean, Solution.lean, comparator.json, formalization.yaml.
7. Fix CI (actions/cache v5), run leanchecker gate.
8. Preflight (Palomar submission workflow, mode: full) → fix any failures.
9. Commit + push, record SHA, submit via agent protocol, monitor, review,
   register (with user consent).
10. Post-registration: add supervisor co-author version; clean up docs.