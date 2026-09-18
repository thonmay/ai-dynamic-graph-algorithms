---
name: elte-bsc-thesis-30-point-audit
description: Conduct the full ELTE Faculty of Informatics BSc thesis 30-point point-by-point audit from the final PDF, editable thesis source, approved proposal, code, tests, and execution-demo evidence. Use when a student or supervisor needs the official seven-criterion score, an evidence-linked provisional score before the live demo, concrete score-changing corrections, or a tailored execution-demo checklist. Do not use for consultation checkpoints, MSc theses, or a generic proofreading review.
---

# ELTE BSc Thesis 30 Point Audit

Audit the submitted work as an evidence chain, not as an impressionistic reading. Apply the updated point-by-point form as thirty binary one-point decisions, use the official assessment guide to interpret them, and apply Gregory Morse's current published supervision requirements as project-specific operational guidance.

## Non-negotiable rules

- Treat the approved proposal as the baseline promise. Record approved scope changes separately; do not silently replace the promise with what was eventually built.
- Use the editable thesis source for substantive review and the submitted PDF for final appearance, pagination, margins, figure legibility, and submission-state verification.
- Require the code at a fixed revision and use it to substantiate difficulty, design fidelity, realization, testing, and documented limitations.
- Do not award partial points. Each rubric item is either `Awarded (1)`, `Lost (0)`, `Pending demo`, or `Unverified input`.
- Distinguish an auditor-input omission from a submission defect. `Unverified input` is not a zero unless the item is genuinely absent from the student's intended submission.
- Do not finalize a total while any item is pending or unverified. Report confirmed points, lost points, pending points, and the possible score range.
- Apply the zero-category rule: if any of the seven criterion totals is definitely zero, the official total is zero. Still show the raw thirty-point subtotal for diagnosis.
- Do not turn “as applicable” into a free point. Test the project-appropriate equivalent and explain it.
- Propagate one underlying defect only when it independently violates another rubric item. Cite the separate criterion-level consequence each time; never apply an automatic global penalty.
- Do not sign the declaration or make the supervisor's legal/academic-integrity decision. Give an evidence-based `Support`, `Do not support`, or `Supervisor decision required` recommendation.

## Authority and freshness

Read [references/00-authorities-and-scoring.md](references/00-authorities-and-scoring.md) before every audit. If internet access is available, check the current official and supervisor sources because policy and submission rules can change. Record retrieval dates and any source drift in the audit.

## Required input package

Request or locate:

1. final submitted thesis PDF;
2. same-revision editable thesis source:
   - LaTeX: complete project/archive including `.tex`, bibliography data, figures, class/style files, and build instructions;
   - Word: `.docx`;
   - Google Docs: local `.docx` export plus the matching PDF; a live link is supplementary, not a substitute;
3. approved proposal/registration PDF and any documented scope changes;
4. complete code repository/archive at a named commit or immutable snapshot, including dependency/environment manifests and available history;
5. tests, results, datasets or safe representative fixtures, and build/run instructions;
6. the three registered final-exam topics and their subtopics;
7. the signed AI-use declaration and any required point-of-use disclosures;
8. prior checkpoint decisions, milestone history, and documented approvals relevant to ownership, process, or scope;
9. the supervisor's later execution-demo observations, when finalizing criterion 7.

Read [references/01-intake-and-parity.md](references/01-intake-and-parity.md) for completeness, safe extraction, source/PDF parity, and format-specific checks.

## Audit sequence

Follow this order. Preserve stable item IDs `C1.1` through `C7.6` across revisions.

### Stage 0: Freeze and inventory evidence

- Hash or otherwise identify every supplied artifact and record the code revision.
- Decide whether each missing item is absent from the student's package or merely not supplied to the auditor.
- Render/compile the editable source and compare it with the submitted PDF.
- Stop an exact final score when substantive source/PDF parity cannot be established.
- Build a promise matrix with one row for every proposal commitment, complex feature, registered exam subtopic, major requirement, and approved change.
- Record checkpoint/deadline/communication evidence separately from product quality; do not invent an unlisted thirty-first point.

### Stage 1: Difficulty and contribution, 4 points

Read [references/02-difficulty-and-propagation.md](references/02-difficulty-and-propagation.md). For the three selected topics, read only the matching headings in [references/03-exam-topic-evidence.md](references/03-exam-topic-evidence.md).

Score:

- `C1.1` thesis-level difficulty plus authentic coverage of exactly three registered exam topics and their relevant subtopics;
- `C1.2` non-trivial algorithm or approach, justified and cited;
- `C1.3` integration across components, tools, platforms, or a defensible project-equivalent integration burden;
- `C1.4` data/persistence or larger-system/environment context, as applicable to the project.

Judge student-authored substance, not dependency feature lists, generated code, boilerplate, or prose volume.

### Stage 2: Structure, language, and appearance, 4 points

Read [references/04-structure-and-appearance.md](references/04-structure-and-appearance.md).

Score:

- `C2.1` compulsory parts;
- `C2.2` logical structure and internal consistency;
- `C2.3` edited text, numbering, styles, captions, margins, and legible balanced visuals;
- `C2.4` academic language, grammar, citation, quotation, and source attribution.

Render every PDF page. Use geometry/text inspection for systematic defects, page images for visual judgment, and higher-resolution inspection for every flagged or uncertain page. A sampling-only pass cannot support a final `C2.3` award.

### Stage 3: User documentation, 4 points

Read [references/05-user-documentation.md](references/05-user-documentation.md).

Score `C3.1` through `C3.4` exactly as the updated form defines. Cross-check all instructions, screens, messages, roles, and promised workflows against source/code evidence. Do not reward screenshots that conceal an incomplete or non-matching process.

### Stage 4: Solution plan, 4 points

Read [references/06-solution-plan.md](references/06-solution-plan.md).

Score architecture (`C4.1`), data/persistence (`C4.2`), module/class design (`C4.3`), and interaction design (`C4.4`). Treat ten pages as a minimum supervisor requirement, not proof of substance.

### Stage 5: Realization and code, 4 points

Read [references/07-implementation-and-code.md](references/07-implementation-and-code.md).

Score documented implementation decisions (`C5.1`), plan-to-code fidelity and justified language/tool use (`C5.2`), maintainability and reuse (`C5.3`), and control/error/resource handling plus limitations (`C5.4`). Inspect the actual code and separate student work from generated, vendored, scaffolded, or third-party material.

### Stage 6: Testing, 4 points

Read [references/08-testing.md](references/08-testing.md).

Score plan/cases (`C6.1`), functional and integration results (`C6.2`), non-functional/scalability evidence (`C6.3`), and lessons/correctness analysis (`C6.4`). Re-run safe, self-contained tests when feasible, but do not turn inability to access production services, private accounts, or devices into a fabricated result.

### Stage 7: Program execution, 6 points

Read [references/09-execution-demo.md](references/09-execution-demo.md).

- Before the demo, assign a definite zero where documentary or code evidence already proves a promised capability is absent or impossible.
- Otherwise leave positive execution points as `Pending demo`; do not award them solely from claims, screenshots, or static code.
- Generate a project-specific manual demo sheet for `C7.1` through `C7.6`, including actions, data, expected evidence, pass condition, and observation field.
- Finalize those points only from direct supervisor observation or comparably direct, trustworthy evidence explicitly accepted by the supervisor.

### Stage 8: Cross-check and report

- Reconcile every rubric decision against the promise matrix and evidence ledger.
- Search for contradictions across proposal, thesis source, submitted PDF, code, tests, AI declaration, and demo observations.
- Recalculate each criterion, raw subtotal, zero-category rule, official total, and grade band independently.
- Read [references/10-report-schema.md](references/10-report-schema.md) and emit the complete report. Every lost point must include a specific defect, evidence pointer, and addressable repair. Separate score-changing corrections from non-scoring suggestions.

## Audit conduct

- Use precise page, section, figure, table, file, symbol, test, commit, or demo-step pointers. Do not write vague comments such as “needs more detail.”
- State the smallest correction that could change a zero to one, without promising that it will do so until re-audited.
- Treat length, bibliography counts, diagrams, and line counts as gates or supporting signals where the supervisor guidance makes them requirements; never mistake quantity for quality.
- Do not use AI detectors or prose style alone to allege authorship misconduct. Report verifiable disclosure mismatches and refer integrity decisions to the supervisor.
- Do not expose registered exam-topic labels as artificial headings the student must add to the thesis. Verify the mapping privately; the thesis should integrate the material naturally.
- Preserve the student's files. Execute untrusted code only in an appropriate isolated environment and never with production credentials, destructive data, paid services, or uncontrolled external side effects.
