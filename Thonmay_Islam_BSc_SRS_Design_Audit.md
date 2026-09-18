# ELTE IK BSc Thesis Checkpoint Audit

**Student:** Thonmay Md Thoriqul Islam (FFR8A9)  
**Thesis:** *AI-Assisted Discovery of Dynamic Graph Algorithms via Evolutionary Code Repair*  
**Supervisor:** Gregory Reynolds Morse  
**Audit date:** 17 September 2026  
**Checkpoints:** 2 - Requirements/SRS; 3 - Architecture and software design

## Overall verdict

| Checkpoint | Result | Main reason |
|---|---|---|
| Requirements / SRS | **Insufficient - Fail** | The five-page concept specification does not translate the three registered contributions into numbered, testable requirements, detailed failure scenarios, measurable quality targets, and acceptance evidence. |
| Architecture / design | **Insufficient - Fail** | The prose volume is adequate, but all five referenced diagrams - including the mandatory class diagram - are absent, the promised UI is replaced by a CLI without an evidenced scope change, and central verification and isolation claims are technically unsound or contradictory. |

The topic is promising and the trusted-verifier idea is a useful foundation. However, the supplied package is not yet a stable specification from which the promised system can be implemented and evaluated.

## Registered promise

The submitted Thesis Topic Registration Form, dated 12 May 2026, identifies exactly three core contributions:

1. **Research tool UI framework.** An interactive platform for managing the evolutionary population, visualizing generation history, failure patterns, and efficiency metrics, and steering the search. The completion signal is an end-to-end UI demonstration that can launch, monitor, and replay a multi-generation run.
2. **Isomorphism-aware dynamic graph verification engine.** A checker covering all non-isomorphic digraphs up to a stated size, applying possible edge operations and comparing candidate behavior with offline recomputation. The completion signal is acceptance of known-good algorithms and rejection of known-bad mutations with zero false negatives for `n <= 5`.
3. **Custom cooperative agents with optional dynamic agent generation.** Domain-specialized agents performing code repair from structured failure reflection, with optional generation of new agents after a plateau. The completion signal is discovery of a correct dynamic BFS algorithm within a bounded number of generations without human intervention.

The registered deliverables are an executable research tool **with UI**, source code, documentation, and an experimental evaluation on a tiered set of dynamic graph problems.

---

# Checkpoint 2 - Requirements / SRS

## Checkpoint result: Insufficient

## Deadline status: Not assessed

The topic form was submitted on 12 May 2026, which is consistent with the 15 May topic deadline for a January final-examination cycle. The SRS is dated July 2026, but a document date is not proof of its actual delivery date. The intended examination session and the Teams/Overleaf submission timestamp were not supplied.

Official checkpoint-2 deadlines are:

- 1 July for a January final examination.
- 1 December for a June final examination.
- Current supervisor guidance provides a 14 December grace deadline for the applicable current planning cycle.

Sources: [ELTE BSc thesis-consultation deadlines](https://www.inf.elte.hu/dstore/document/227123/BSc%20Thesis%20consultations%20-%20deadlines%202024%20.pdf) and [current BSc Thesis Workflow Guidance](https://grm.web.elte.hu/).

## Evidence reviewed

- `thesis-specs.tex`, dated July 2026.
- Successful five-page A4 build of the SRS.
- Figure 1: use-case diagram.
- Table 1: eight Given-When-Then user stories (`US-01` through `US-08`).
- Four brief non-functional-requirement bullets.
- `thesis-prism-upload.zip`, including the separate `design-doc.tex` and thesis scaffold.
- Submitted Thesis Topic Registration Form, dated 12 May 2026, containing the title, three contributions, completion signals, and deliverables.

Unavailable or unverified:

- Any approved scope-change request.
- Intended final-examination session.
- Actual checkpoint submission timestamps.
- Version identifier and revision history for the SRS.
- Supervisor-access path for the live editable document.

## Mandatory gates

| ID | Criterion | Status | Evidence | Finding |
|---|---|---|---|---|
| C1 | Purpose, scope, actors, and boundary | **Fail** | SRS sections 1-2; Figure 1 | Purpose and two actors are visible, but assumptions, explicit exclusions, terminology, dependency boundaries, and what the student builds versus reuses are incomplete. |
| C2 | Traceability to the registered promise | **Fail** | Topic form contributions 1-3; SRS sections 2-4 | No contribution-to-requirement/evidence matrix exists. The SRS postpones a richer UI despite the registered UI deliverable and leaves cooperation/dynamic-agent creation undecided despite contribution 3. |
| C3 | Functional requirements | **Fail** | Table 1, `US-01`-`US-08` | These are broad capabilities, not precise atomic requirements. Verification bounds, legal operations, agent protocols, repair, selection, stopping, replay, steering, and resumption remain undefined. |
| C4 | Detailed scenarios | **Fail** | Figure 1; Table 1 | Each story contains one short happy-path Given-When-Then only. Alternate, invalid, boundary, timeout, crash, permission, recovery, and partial-result flows are absent. |
| C5 | Acceptance criteria and evidence | **Fail** | Topic-form completion signals; SRS sections 2-4 | The topic form provides headline completion signals, but the SRS does not refine them into named tests, demonstrations, thresholds, output artifacts, and failure criteria. |
| C6 | Data and business rules | **Fail** | SRS persistence paragraph | No requirements-level model covers runs, generations, candidates, parents, reflections, failures, metrics, ownership, uniqueness, retention, or crash-safe lifecycle. |
| C7 | Interfaces and roles | **Fail** | Figure 1; `US-01`-`US-05` | Student and supervisor are separate actors, but the planned local CLI has no defined sharing or role model. UI behavior, command schemas, file formats, model-provider interface, and failure outputs are incomplete. |
| C8 | Measurable quality requirements | **Fail** | SRS section 4 | Statements such as "about n <= 5," configurable timeouts, portability, and usability are not measurable targets. Security, privacy, scalability, maintainability, accessibility, and reproducibility are missing or unquantified. |
| C9 | Planning and feasibility | **Fail** | SRS section 2 | Useful early decisions exist, but there is no priority/release split, risk register, resource/API-cost budget, platform constraint, dependency fallback, or feasibility experiment. |
| C10 | Testability and internal consistency | **Fail** | SRS versus topic form and design document | The UI promise is reduced to a CLI; cooperative agents are left undecided; "LLM-agnostic" conflicts with OpenCode-specific design; exhaustive sequence coverage has no finite bound. |
| C11 | Reuse in final Developer Documentation | Pass | Entire SRS | The document is project-specific and its story identifiers can form part of a revised canonical requirements chapter. |
| C12 | Supervisor access and delivery | **Unverified** | July 2026 date only | No version number, revision history, canonical-source statement, or Overleaf/Teams/SharePoint access statement is supplied. |

## Required corrections

### 1. Trace the three registered contributions exactly

**Defect:** The registered promises are not mapped to the SRS, and two have already drifted: the interactive UI becomes an optional later decision, while the cooperative/dynamic-agent organization is deferred as a research question.

**Why it blocks:** A checkpoint specification must make the registered deliverables judgeable; it cannot silently substitute a CLI or an unspecified agent experiment.

**Exact repair:** Add a promise matrix with one row for each registered contribution and deliverable and columns for numbered requirements, scenarios, data, design components, acceptance method, and evidence artifact. Restore the UI and cooperative-agent promises, or attach written approval for the changed scope.

**Passing evidence:** All three topic-form contributions appear verbatim and trace to requirements and observable completion signals, with any approved deviations clearly identified.

### 2. Replace broad stories with atomic requirements

**Defect:** `US-01`-`US-08` do not define sufficient behavior to implement or test the system.

**Why it blocks:** Developers and evaluators would have to invent configuration validation, legal graph operations, stopping rules, error handling, and replay semantics.

**Exact repair:** Retain the user stories, but add stable IDs such as `FR-UI-01`, `FR-VER-01`, `FR-EVO-01`, and `FR-AGENT-01`. For each, define input, precondition, behavior, output, rejection/error behavior, and priority. Add detailed scenarios for launch, pause/stop, resume, replay, agent plateau, API failure, candidate timeout, verifier disagreement, invalid graph operation, and all-candidates-failed.

**Passing evidence:** Every Must requirement has an unambiguous expected result and at least one detailed normal or failure scenario.

### 3. Define the bounded verification experiment precisely

**Defect:** "All non-isomorphic digraphs" and "operation sequences" are not a finite test specification.

**Why it blocks:** The coverage claim cannot be reproduced or evaluated without graph and sequence semantics.

**Exact repair:** Define whether graphs are simple, loop-free, rooted, connected, or allow antiparallel arcs; define legal/illegal insertions and deletions; give the maximum sequence length; state whether every sequence or only every one-step operation is enumerated; define the sampling distribution and seed policy beyond the exhaustive bound.

**Passing evidence:** A reviewer can calculate the finite test universe for each `n`, reproduce it, and distinguish exhaustive from sampled evidence.

### 4. Turn completion signals into measurable acceptance evidence

**Defect:** The registered signals are not operationalized. "Bounded generations" has no bound, "correct" has no exact oracle, and "zero false negatives" lacks a mutation corpus.

**Why it blocks:** Contributions 2 and 3 cannot be given a binary completion verdict.

**Exact repair:** Specify the maximum generations, population, model-call budget, repeated-run count, seeds, known-good reference set, known-bad mutation set, expected confusion matrix, required UI demonstration, and stored evidence files. State that finite exhaustive testing establishes bounded correctness, not a proof for arbitrary graph size.

**Passing evidence:** Each contribution has a named demonstration/test and explicit pass/fail threshold.

### 5. Specify the cooperative-agent experiment

**Defect:** The topic form promises cooperative agents and optional dynamic agent creation, but the SRS leaves their existence and interaction undecided.

**Why it blocks:** The third principal contribution has no required behavior or evaluable experimental protocol.

**Exact repair:** Define the initial agent roles, messages/artifacts exchanged, cooperation or critic protocol, plateau detector, dynamic-agent creation rule, permissions, budget, and termination. If alternatives are to be compared, define the single-agent and fixed-team baselines and evaluation metrics.

**Passing evidence:** Contribution 3 has reproducible variants, controlled budgets, stored transcripts/results, and a clear success criterion.

### 6. Add measurable quality and security requirements

**Defect:** The NFR section is qualitative and omits qualities central to executing generated code.

**Why it blocks:** Safety, reproducibility, feasibility, and reliability cannot be tested.

**Exact repair:** Add measurable targets for runtime, memory, process count, model/API cost, checkpoint recovery, deterministic verification, UI response time, accessibility, supported operating systems, logging, privacy of code sent to model providers, and sandbox escape resistance.

**Passing evidence:** Every claimed quality has a numerical target, evaluation procedure, or justified N/A statement.

### 7. Establish one canonical requirements source

**Defect:** The standalone SRS is populated while `chapters/03-requirements.tex` remains an empty TODO scaffold.

**Why it blocks:** There are two incompatible requirements baselines.

**Exact repair:** Integrate the revised SRS into the thesis requirements chapter, add version/date/revision history, and state the supervisor-access path.

**Passing evidence:** One dated, versioned source compiles without placeholders and is the source used by the design traceability matrix.

## Comments and suggestions

- The problem statement, bounded verification direction, and trusted-verifier concept are good foundations.
- `UC-06`-`UC-08` describe internal process steps more naturally represented by an activity or sequence diagram than by user use cases.
- The `<<extend>>` relation between verification and reflection is drawn in the wrong UML direction.
- Define the exact dynamic LBFS research question, update/query model, desired complexity, and literature basis. Calling the area an "open problem" is too broad.
- Negative results can be valuable only under a predeclared budget, baseline, repeated-run protocol, and reporting method.

## Scope note

This is a checkpoint-2 content-sufficiency decision only. It is not the consultation-course grade, final thesis score, or judgment of whether the eventual research result will be positive.

---

# Checkpoint 3 - Architecture and software design

## Checkpoint result: Insufficient

## Deadline status: Not assessed

The 12 May topic submission and 2027 thesis year strongly suggest, but do not prove, a January 2027 cycle. If January 2027 applies, the architecture deadline was 10 September 2026; the supplied archive is dated 17 September, but the archive timestamp does not establish when the student first shared the work. If June 2027 applies, the normal deadline is 10 February 2027.

The examination session and actual Teams/Overleaf submission history are therefore required before assigning `On time` or `Late`.

## Evidence reviewed

- `design-doc.tex`, dated September 2026.
- Forced compilation produced 19 pages: title, contents, approximately 16 body pages, and an empty bibliography.
- Five missing-image placeholders:
  - `diagrams/architecture.png`
  - `diagrams/deployment.png`
  - `diagrams/classes.png`
  - `diagrams/loop.png`
  - `diagrams/verification.png`
- Five absent bibliography keys causing six unresolved citation occurrences: `yang2019dynamic`, `karczmarz2023dynamic`, `rose1976algorithmic`, `demetrescu2005dynamic`, and `openai2025codex`.
- Topic Registration Form containing the exact three contributions and their completion signals.
- `chapters/04-design.tex`, which remains a TODO scaffold rather than containing the populated design.
- README acknowledgement that the topic declaration was omitted from the archive and final-examination topics were not selected.

Unavailable or unverified:

- The five referenced design diagrams.
- Thesis Consultation subject-registration confirmation.
- Selected or proposed final-examination topics.
- Approved UI-to-CLI or other scope-change evidence.
- Target examination session and actual design submission timestamp.

## Mandatory gates

| ID | Criterion | Status | Evidence | Finding |
|---|---|---|---|---|
| C1 | Design substance and figures | **Fail** | 19-page forced build; Figures 1-5 | The prose likely meets the ten-page component, but none of the five claimed figures was supplied or visually inspectable. Several pages are substantially occupied by missing-image boxes. |
| C2 | Architecture and separation | **Fail** | Design sections 2.1-2.5 | Layer responsibilities are described, but the claimed verifier/agent/candidate trust boundary is not enforced by the proposed subprocess mechanisms. |
| C3 | Business rules | **Fail** | Design sections 3.1-3.4 | Central DFS/LBFS predicates are incorrect, enforcement ownership is incomplete, and timeout/state policies conflict. |
| C4 | Mandatory class diagram | **Fail** | Figure 3 placeholder; section 4.2 | The mandatory diagram is absent. A prose class table does not establish associations, multiplicities, ownership, or operations. |
| C5 | Data design | **Fail** | Design sections 5.1-5.3 | Files and JSON are described, but run identity, atomicity, schema versioning, uniqueness, lineage, lifecycle, integrity, concurrency, and safe recovery are incomplete. |
| C6 | Interaction design | **Fail** | Topic contribution 1; design sections 6 and 8.4 | The registered interactive UI is replaced by a CLI without approval. No mockups, navigation map, steering interactions, or launch/monitor/replay UI handlers are supplied. |
| C7 | Core logic / scientific model | **Fail** | Design sections 3, 7 and 8.2 | Search, mutation, crossover, dynamic-agent creation, operation enumeration, and verification remain underspecified; several correctness and acceptance rules are unsound. |
| C8 | Requirement and contribution traceability | **Fail** | Table 6; topic contributions 1-3 | The matrix maps stories only to components. It omits data, interactions, acceptance evidence, high-priority requirements, the three registered contributions, and explicit scope deviations. |
| C9 | Design rationale and level | Pass | Design sections 8.4-8.7 | CLI, orchestrator-controlled verification, invariant-oriented comparison, and JSON persistence receive project-specific rationale and some alternatives. |
| C10 | Final-exam topic integration | **Fail** | Design section 9 | The section explicitly defers all planning. Current transition treatment may excuse final registration, but not the absence of a credible provisional mapping. |
| C11 | Thesis Consultation registration | **Unverified** | No evidence supplied | Registration for the Thesis Consultation subject with the supervisor as lecturer is not confirmed. |
| C12 | Internal consistency and implementability | **Fail** | Whole package | Missing diagrams, registered-scope drift, inconsistent states, unsupported isolation, incorrect invariants, undefined algorithms, divergent thesis sources, and broken citations prevent implementation from one stable design. |

## Required corrections

### 1. Supply and validate the design figures

**Defect:** Every figure referenced by `design-doc.tex`, including the mandatory class diagram, is missing from the ZIP.

**Why it blocks:** Figure existence, readability, semantics, and correspondence cannot be audited; the class diagram is an explicit checkpoint requirement.

**Exact repair:** Include a readable architecture/component view, deployment/isolation view, class diagram, evolutionary-loop interaction view, and verification-flow/state view. The class diagram must include key operations, associations, multiplicities, and ownership corresponding to the actual modules.

**Passing evidence:** The unmodified archive compiles without missing-file errors, and all figures are readable at normal PDF size and explained in the text.

### 2. Restore the registered UI or obtain approval for a scope change

**Defect:** The topic form promises an interactive platform that launches, monitors, replays, visualizes, and permits steering. The design instead explains why CLI plus OpenCode replaces a web UI.

**Why it blocks:** This removes registered contribution 1 and a named deliverable.

**Exact repair:** Either design the UI with screen inventory, mockups, navigation, generation-history/failure/metric views, and launch/monitor/replay/steering handlers, or attach an explicit approved change to the registered topic.

**Passing evidence:** Contribution 1 traces to actual interaction diagrams, data, handlers, and an end-to-end UI demonstration - or to documented approval of an equivalent replacement.

### 3. Replace the fictional subprocess sandbox

**Defect:** The design says a restricted `subprocess` environment blocks network access and limits filesystem writes. It does neither. The environment mapping controls environment variables; it is not a security boundary. The selected OpenCode agent also has file and shell capabilities while the design claims it cannot access verifier code.

**Why it blocks:** Generated Python is untrusted, so a false isolation model can corrupt the verifier, read secrets, access the network, or damage files. Python's [`subprocess` documentation](https://docs.python.org/3/library/subprocess.html) describes `env` only as the child-process environment mapping.

**Exact repair:** Use an actual OS isolation mechanism: a rootless container or namespace, non-root identity, disabled network namespace, read-only root filesystem, verifier source not mounted, dedicated writable scratch mount, and CPU/memory/process/output/time limits. Separate the agent workspace from the trusted verifier and expose only a narrow structured interface.

**Passing evidence:** Negative tests demonstrate failure of network access, verifier reads/writes, filesystem escape, process explosion, excessive output, and timeout overrun.

### 4. Correct the scientific invariants and claims

**Defect:** The directed-DFS and LBFS predicates in section 3.1 are not valid general characterizations. A directed DFS tree may legitimately have forward and cross edges. For example, with `r -> a`, `a -> b`, and `r -> b`, the final edge is a valid forward edge although `b` is not a child of `r`. The stated consecutive-earlier-neighbor LBFS rule also fails on ordinary valid LexBFS orderings, such as a four-cycle. Reachability is in scope but has no invariant.

**Why it blocks:** The trusted verifier would reject correct candidates or accept incorrect ones, invalidating the thesis experiment.

**Exact repair:** Replace each predicate with a cited and tested recognition procedure. Define graph representation, root semantics, legal updates, and exact post-update output. Validate the verifier using independent reference algorithms, hand-checked small instances, property tests, and deliberately faulty mutations.

**Passing evidence:** Each target problem has a correct formal predicate, independent oracle, positive/negative test suite, and no unresolved citation.

### 5. Distinguish bounded verification from proof

**Defect:** Sections 8.1-8.3 call exhaustive finite testing a "correctness proof."

**Why it blocks:** Absence of a counterexample for `n <= 5` and bounded sequences does not prove correctness for arbitrary graph size or update length.

**Exact repair:** Report "bounded exhaustive verification" or "no counterexample within the stated bound." Reserve "proof" for a mathematical proof or formal verification covering the claimed input domain.

**Passing evidence:** Every correctness claim explicitly states its graph-size and sequence bounds and separates testing evidence from proof.

### 6. Complete the evolutionary and cooperative-agent design

**Defect:** Parent selection is described, but mutation, crossover, prompt/schema contracts, cooperative-agent message flow, plateau detection, dynamic-agent generation, budget allocation, and recovery are not implementable from the design.

**Why it blocks:** Registered contribution 3 remains decorative rather than designed.

**Exact repair:** Define agent roles and interfaces, structured reflection schema, candidate-generation and repair operators, parent/multi-parent lineage, selection ordering, diversity mechanism, plateau metric/window, dynamic-agent creation/retirement, budgets, and terminal behavior. Include a sequence/activity diagram.

**Passing evidence:** The principal source modules and interfaces can be implemented without inventing the core agent protocol.

### 7. Repair acceptance and efficiency semantics

**Defect:** Section 8.2 accepts a candidate when its "efficiency ratio is positive," followed by the statement that it performs more work than recomputation. Almost every nonzero ratio is positive, and doing more work is not an efficiency improvement.

**Why it blocks:** The acceptance decision is mathematically undefined or reversed.

**Exact repair:** Define, for example,

```text
work_ratio = candidate_work / offline_recomputation_work
```

and state the required threshold, such as `< 1` for improvement. Define aggregation across operations and graphs, treatment of ties, wall-clock versus instrumented work, and statistical reporting over runs.

**Passing evidence:** The formula, units, benchmark population, and threshold are identical in requirements, design, implementation plan, and tests.

### 8. Resolve state and persistence contradictions

**Defect:** The example JSON marks `PASS` with fitness `0.85` and 17/20 tests; the state table classifies timeout as `CRASH`, while section 6.4 records it as `FAIL`; crossover is mentioned while the schema has only one `parent_id`; safe checkpoint writes are unspecified.

**Why it blocks:** State, lineage, resumption, and result interpretation would differ between components.

**Exact repair:** Define one state machine with transition guards and terminal states. Add run IDs, candidate uniqueness, schema version, multi-parent lineage, atomic temporary-write/rename, generation commit marker, checksum, partial-generation recovery, retention, and compatibility rules.

**Passing evidence:** State table, class model, JSON schema, interaction diagrams, and recovery tests agree exactly.

### 9. Build proper traceability to the topic form

**Defect:** Table 6 links only user stories to components, while section 8.1 replaces the registered three contributions with two categories of positive/negative experimental results.

**Why it blocks:** None of the registered promises can be followed through the implementation and acceptance plan.

**Exact repair:** Add rows for every high-priority requirement and each registered contribution, with columns for components/classes, interaction, data, acceptance evidence, and planned implementation/test sections. Record the invariant-versus-offline-comparison refinement explicitly rather than silently changing the verifier contract.

**Passing evidence:** No contribution disappears, no component is orphaned, and every registered completion signal has a concrete evidence artifact.

### 10. Repair the canonical document, citations, topics, and administration

**Defect:** `design-doc.tex` is populated while `chapters/04-design.tex` is an empty TODO scaffold; five cited keys are absent; examination topics are wholly deferred; Thesis Consultation registration is unverified.

**Why it blocks:** There is no single compilable design baseline, evidence chain, or complete checkpoint package.

**Exact repair:** Integrate the design into `chapters/04-design.tex`; attach the topic declaration to the thesis project; correct and verify all references; add a credible provisional map to exactly three natural exam topics; supply subject-registration confirmation; add version/date/revision identity and sharing path.

**Passing evidence:** The canonical archive compiles normally with no missing assets, TODO checkpoint content, unresolved citations/references, or unexplained divergence.

## Comments and suggestions

- The layered decomposition, candidate lifecycle, persistence outline, and verifier trust concept are useful starting material.
- The thesis should sharply distinguish four claims: correctness of the research tool, bounded verification of generated candidates, experimental effectiveness of the search process, and a mathematical proof of an algorithm.
- The SRS claims vendor independence while the design hardcodes OpenCode commands and named providers. Keep these behind an adapter or revise the portability promise.
- The topic form says comparison with offline recomputation, while the SRS moves to invariant checking because BFS/DFS outputs may be non-unique. This can be a sound refinement, but it must be documented: compare semantic properties or canonical quantities produced by an independent offline oracle, not raw tree equality.
- If AI was used to draft thesis text, diagrams, or infrastructure code, add point-of-use disclosure and complete the separate declaration honestly. Do not conflate authoring assistance with candidate programs generated as experimental output by the system itself. See the [current supervisor guidance](https://grm.web.elte.hu/).

## Scope note

This is a checkpoint-3 content-sufficiency decision only. It is not the consultation-course grade, a 30-point final-thesis score, or a judgment that the proposed research cannot succeed.

---

# Re-audit priority order

The shortest route to a passing re-audit is:

1. Freeze the exact three topic-form contributions and obtain approval for any change.
2. Restore and design the interactive UI.
3. Correct the DFS/LBFS oracles and bounded-correctness claims.
4. Replace the subprocess pseudo-sandbox with a real isolation architecture.
5. Convert the SRS into numbered requirements with detailed failure scenarios and measurable acceptance evidence.
6. Supply the missing diagrams, especially the class diagram.
7. Complete the cooperative-agent protocol, state machine, persistence guarantees, and contribution traceability.
8. Integrate the SRS/design into one canonical thesis source and eliminate missing assets, TODOs, and broken citations.
