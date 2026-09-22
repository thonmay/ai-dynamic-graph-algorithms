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
  Challenge + the project modules. Zero `sorry`/`sorryAx`/`Lean.ofReduceBool`;
  only propext/Classical.choice/Quot.sound.
- `comparator.json` — EXACT 4-key shape (from CONTRIBUTING 2.3):
  `{"challenge_module": "Challenge", "solution_module": "Solution",
    "theorem_names": ["Challenge.<thm>", ...],  -- dotted module-qualified
    "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"]}`.
  No other keys. ≤1 MiB. `definition_names` optional (default []),
  `enable_nanoda` ignored (Palomar always forces NanoDa on).
- `formalization.yaml` (v0.4) — REQUIRED fields: `version: "v0.4"`,
  `project.name` (≤300), `project.description` (≤10k, the public abstract),
  `project.authors` (nonempty humans), `project.license` (exact SPDX
  match to root LICENSE file = Apache-2.0), `project.responsible_maintainers`
  (nonempty humans), `classification.arxiv` (1-8 distinct, cs.DS + math.CO
  verified present in Palomar taxonomies json), `classification.msc2020`
  (≤8 distinct, 05C85 + 68Q25 + 68W40 verified; 68Q25+68W40 near-dup, drop
  one for cleanliness), `automation.methods` (nonempty, list of {method: ...};
  AI-assisted with manual review + leanchecker), `review.status` (nonempty),
  `sources` (nonempty; ONE origin alternative — here
  `{type: original-proof, relationship: other}` since this first presents
  the dynamic-MCS result; any background sources with relationship
  `background`/`other`).
- `lakefile.toml` + `lake-manifest.json` + `lean-toolchain`: present, AND add
  `[[lean_lib]]` entries so Challenge/Solution are buildable roots:
  `[[lean_lib]] name = "Challenge" roots = ["Challenge"]`,
  `[[lean_lib]] name = "Solution" roots = ["Solution"]`.
- ROOT `LICENSE` file (Apache-2.0) — HARD REQUIREMENT, must match
  project.license exactly; missing/multiple/mismatched fails mechanical
  verification before editorial review.
- CI: fix the coverage gap (import artifact modules into the root target so
  leanchecker covers all 12 + Challenge/Solution); change
  `tool-cache: true` → `preinstalled-runtimes: true` (deprecation notice).
  No cache-version bump needed (Node 20 warning already gone).
- Confirm no compiled artifacts committed (.olean/.ilean/.so); repo checkout
  ≤ 500 MiB; mathlib pin in lakefile/lake-manifest matches lean-toolchain
  v4.34.0 (canonical toolchain-match rule); add `.beam/` to `.gitignore`.

## Submission flow (agent protocol, no browser) — REVISED per llms.txt + CONTRIBUTING

Preconditions:
- Confirm WITH USER before submitting: show repo, commit, comparator path,
  and the authorization_relationship answer ("maintainer") — get agreement.
- One submission at a time (429 if others in flight); cooldown between starts.

Sequence:
0. Commit + push the final snapshot. Record full 40-char SHA
   (`git rev-parse HEAD`).
1. Commit + push final snapshot; record full 40-char SHA.
2. PREREG the submit body:
   `POST https://submit.palomar-registry.org/api/submit`
   `{"repository": "thonmay/thesis-lean", "commit": "<SHA>",
     "comparator_config_path": "comparator.json",
     "authorization_relationship": "maintainer"}`  (omit existing_id for new)
   → `pending_secret` + `challenge`.
   IMPORTANT: steps 1-4 are ONE SITTING. pending_secret dies after 15 min.
3. Create tag at the commit:
   `gh api -X POST repos/thonmay/thesis-lean/git/refs \
     -f ref=refs/tags/palomar-verify-<challenge> -f sha=<SHA>`
4. Create a SECRET gist carrying the challenge, within a minute of intake:
   `echo '{"public":false,"files":{"palomar.txt":{"content":"<challenge>"}}}' \
     | gh api -X POST gists --input -`  → gist_id
5. `POST /api/verify {"pending_secret": "...", "gist_id": "..."}`
   → `submission_id` + `access_token` (10 attempts total, taken before checks).
6. Delete tag + gist immediately:
   `gh api -X DELETE repos/thonmay/thesis-lean/git/refs/tags/palomar-verify-<challenge>`
   `gh api -X DELETE gists/<gist_id>`
7. Monitor `GET /api/submission` (Bearer token) once a minute while running,
   every 5 min while awaiting-review/review-ready. Poll at human pace, not a
   tight loop.
8. Review `GET /api/review` (Bearer token). PRIVATE until registered — do
   not paste publicly. Show the user, discuss.
9. Register `POST /register {"review_sha256": "<digest from review>"}`
   ONLY after showing the user the review, explaining what registration
   publishes (repo, commit, review, immutable preservation tags), and getting
   their explicit instruction. Consent is to the review the user read.
   The access_token is a credential — treat as secret.
10. Add supervisor as co-author later: new commit (formalization.yaml
    authors += Morse) → NEW full submission with `existing_id` =
    PALOMAR-... id. Must retain repo/project/comparator paths; every version
    re-proves write access. Cheaper alternative: put both authors in v1 now
    if Morse agrees.

## Preflight (REVISED) — runs BEFORE submit, AFTER commit+push

- From the exact repo+commit, run
  `PalomarRegistry/PalomarSubmission/.github/workflows/submission.yml`
  (reusable workflow, `mode: full`) via a dispatched run or the provided
  helper. Inputs:
  - `repository`: thonmay/thesis-lean
  - `commit`: the full 40-char SHA (after push — it checks out the pushed commit)
  - `pipeline_commit`: full SHA of PalomarSubmission HEAD, PINNED to the same
    commit as the workflow's `uses:` ref
  - `request_id`: caller-chosen lowercase identifier
  - `mode`: full
  - `options`: JSON carrying `comparator_config_path` (and project_path/
    formalization_metadata_path only if non-default)
- `palomar-standard-v1` is report metadata (resource profile), NOT a field in
  comparator.json — no repo change needed.
- Continue to submit only when the report says `status: pass`. A passing
  preflight is advisory (does not run Challenge rendering or review).

## Team/ownership

- Author: Md Thoriqul Islam Thonmay (submitter, maintainer relationship).
- Co-author to add later: Gregory Morse (as new version).
- AI disclosure: formalization AI-assisted (lean-prover agent swarm), proofs
  manually reviewed and independently re-checked with leanchecker; document in
  formalization.yaml per ELTE AI usage policy.

## Risks / open items (REVISED after 4-subagent review 2026-09-22)

RESOLVED by review:
- Repo visibility: `thonmay/thesis-lean` now PUBLIC (verified unauth via
  raw.githubusercontent 200 + git ls-remote; gh shows PUBLIC).
- Node 20 CI warning: ALREADY RESOLVED — it came from `docgen-action`'s
  monolithic `actions/cache` step (SHA 5a3ec84...), removed in commit
  `f438943`. Does NOT come from lean-action (v1 already uses cache@v5) and
  NOT from checkout@v4 (workflow never used it). No cache "bump" is possible
  or needed. Only cosmetic notice left: free-disk-space `tool-cache` input
  deprecated, renamed `preinstalled-runtimes` (lean_action_ci.yml:23).

OPEN (folded into Steps below):
- SPACE CLAIM: formalize O(n²) NOT O(n+m). Exec `Adj n = List (List Bool)`
  is an n×n matrix = O(n²) cells; bitmask gen003 is n words of n bits =
  O(n²). The prose O(n+m) space is false for our representation. Headline
  space bound: fixed n×n adjacency + n-length order/pos ⇒ O(n²).
- COMPLEXITY HONESTY: the abstract `greedySuffix` is noncomputable
  (Classical.choose) and honestly O(n²). Do NOT claim it runs in
  O(n + m_suffix). Instead:
  * PROBE bounds are computable on the abstract model: `firstBreakAux` is
    structural recursion; probe cost = recursion depth. Insertion probe
    O(k) (k = laterPos - earlierPos), deletion check O(n) as one
    cardinality recheck.
  * For the supervisor's O(m+n) worst-case headline: define an explicit
    COST MEASURE `insertCost`/`deleteCost` = probe steps + suffix length +
    mSuffix (edge pair-count), realize it via the bucket/bitmask rep (the
    bridge `bestPick_IsMCSNext` shows bestPick = max-card-min-id = bucket
    result). State `∃ c, insertCost ≤ c*(n + m)` with m = edgeCount
    (undirected pair-count / 2, with evenness lemma). Document clearly in
    formalization.yaml that this measure is realized by the bitmask
    implementation, not by the noncomputable abstract model.
  * Reject gen003_c02 periodic rebuild for headlines: amortized
    O((n+m)/64) needs a division bound; keep it as a documented extension.
- Challenge self-containment: the Challenge MUST redefine every type it
  states a theorem about in Mathlib-only code. It may NOT import ANY
  project source (not even Formal_gen001c01, despite it being
  Mathlib-only — the rule is about source files in the import closure).
  The Solution's compared declarations must match the Challenge's
  redefinitions exactly (prove by exact/definitional equality or re-prove
  in the Challenge's namespace).
- K = 0 / empty window edge cases: split out; `u = v` update is identity.
  No division in bounds. `ℕ` difference `laterPos - earlierPos` is safe.
- CI GAP: the root target `ThesisLean.lean` imports only 3 of 12 modules
  (Basic, Formal_gen001c01, Formal_gen003c01), so Bridge/Card/Exec/McsInv
  are neither built nor leanchecker-verified in CI. Fix: import the
  artifact module(s) into the root target (or add a build+leanchecker step
  for Challenge.lean/Solution.lean) so the kernel-check gate covers the
  Palomar artifact.
- Everything else in the original Risks section below is superseded by the
  Step-by-step details added in Steps 6-9.

## Theorem classification (from Formal_gen003c01, for comparator/narrative)

Headline (go in Challenge + comparator):
- `init_valid` — init produces a valid MCS ordering.
- `greedySuffix_full` — regreedy of the whole suffix yields a valid ordering.
- `insert_update_valid` — INCREMENTAL correctness.
- `delete_update_valid` — DECREMENTAL correctness.
- `ordering_of_steps_legal` — step-by-step construction stays legal.
- `update_from_prefix` — update preserves the prefix (shared data structure).
- Bridge: `mcsOrder_eq_greedySuffix` (from BridgeAssembly).

Dependencies (NOT headline; the 30-ish support lemmas):
- firstBreak/firstBreakWindow probe lemmas (firstBreak_some/none, firstBreakAux_*,
  getElem_drop_order, insert_break_iff, deletionBreaks_true_iff)
- flip lemmas (flip_pair_ne, adj_flip_ins, neigh_flip_insert/delete,
  neigh_eq_flip_both_chosen, IsMCSNext_of_drop, IsMCSNext_of_eq_neigh_on,
  IsMCSNext_of_unique_max)
- order internals (laterPos/laterVert/earlierVert + get/eq lemmas,
  earlier_ne_later, earlierPos_lt_laterPos, idxOf_*_Vert,
  bothend_in_take_of_lt_laterPos, legal_after_laterPos, legal_middle_delete,
  order_toFinset_univ, neigh_alt, validState_iff)

TODO (new, headline): incremental complexity, decremental complexity.

## Steps (implementation order)

1. Clean up scratch/bak files in ThesisLean/. DONE (all 20 untracked removed).
2. Classify the 36 theorems: headline vs dependency (for comparator +
   formalization.yaml narrative). DONE (see above).
3. Formalize complexity cost model + incremental complexity theorem:
   firstBreakAux recursion-depth probe cost (O(k)), explicit insertCost
   measure (probe + suffix length + mSuffix pair-count), witness bound
   `∃ c, insertCost ≤ c*(n + m)` with edgeCount + evenness lemma. Space:
   O(n²).
4. Formalize decremental complexity theorem: deletion probe O(n) (cardinality
   recheck), deleteCost measure, witness bound.
5. Extend static bridge per-flip (cheap variant, NOT new executable updater):
   prove Exec.insertEdge/deleteEdge + recompute keeps IsMCSOrdering, using
   abstract insert_update_valid/delete_update_valid (the "maintains an MCS
   order" headlines).
6. Fix CI gap: import artifact modules into root target (or build+leanchecker
   Challenge/Solution explicitly) so kernel gate covers all modules. Also
   tool-cache → preinstalled-runtimes (cosmetic). Commit + push.
7. Package: root LICENSE (Apache-2.0), lakefile [[lean_lib]] for
   Challenge/Solution, Challenge.lean (self-contained, Mathlib-only,
   headline statements with sorry), Solution.lean (proved, same names/types),
   comparator.json (exact 4-key), formalization.yaml (v0.4, all required
   fields, sources original origin). Commit + push.
8. Preflight AFTER push: run PalomarSubmission workflow (mode: full) against
   the exact commit with pipeline_commit pin + request_id + options.
   Fix failures until status: pass.
9. Submit via agent protocol (one sitting, guardrails per Submission flow
   REVISED): POST /api/submit → tag → secret gist (within 1 min) →
   /api/verify → delete tag+gist → monitor → review → show user →
   register (review_sha256). User consent confirmed before submit AND before
   register.
10. Post-registration: co-author version (Morse) if not in v1; clean up docs.