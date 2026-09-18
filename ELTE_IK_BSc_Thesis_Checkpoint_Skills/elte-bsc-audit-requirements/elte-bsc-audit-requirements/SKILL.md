---
name: elte-bsc-audit-requirements
description: "Audit ELTE Faculty of Informatics BSc thesis consultation checkpoint 2: the detailed software requirements and planning package. Use when a student or supervisor needs a binary Sufficient/Insufficient review of an SRS, use cases, user stories, acceptance criteria, or requirements traceability. Do not use for topic registration, architecture, implementation, completed-thesis review, or 30-point final grading."
---

# ELTE IK BSc checkpoint 2 audit

Evaluate whether the detailed requirements package is sufficient for the second official BSc consultation checkpoint and reusable in the final Developer Documentation.

## Required references

Read both files completely before evaluating:

- [references/checkpoint-criteria.md](references/checkpoint-criteria.md) for the mandatory gates.
- [references/source-policy.md](references/source-policy.md) for source precedence, dates, and the grading boundary.

When internet access is available, check the linked official deadline PDF and Gregory Morse's BSc Thesis Workflow Guidance for material changes. Do not add university-process requirements from unrelated sources.

## Evidence intake

Seek the current requirements document plus the approved or submitted topic proposal and its three contributions. Record the intended final-exam session, target semester, submission date, and any approved scope change or exception. If the student used Word or Overleaf, verify that the supervisor-access method is stated; do not require account credentials.

Inspect all pages, diagrams, tables, and appendices. Render PDF or Word files when layout affects legibility. Preserve the student's artifacts and do not edit them unless explicitly asked.

Missing evidence for a mandatory gate is `Unverified`, not a presumed pass. Any `Fail` or `Unverified` mandatory gate makes the result `Insufficient`.

## Decision rule

- `Sufficient`: every applicable mandatory gate is `Pass` or a justified `N/A`.
- `Insufficient`: at least one mandatory gate is `Fail` or `Unverified`.

Use `N/A` only for conditional domain elements such as a database or a GUI, never to avoid defining actors, behavior, acceptance, interfaces, constraints, or traceability.

Report deadline status separately as `On time`, `Late`, or `Not assessed`. Do not convert this audit into the official three-point consultation grade or the later 30-point thesis grade.

## Audit method

1. Build a trace from the approved problem and exactly three headline contributions to numbered requirements, scenarios, and measurable acceptance evidence.
2. Check functional coverage through either detailed use cases or user stories. A diagram without narratives, or stories without testable outcomes, is insufficient.
3. Check alternate, invalid, boundary, permission, and failure behavior where relevant; happy-path prose alone is not a detailed specification.
4. Check non-functional requirements only where material to the system, but require measurable statements for claimed performance, security, reliability, scalability, usability, privacy, or compatibility.
5. Check external interfaces, data rules, roles, assumptions, dependencies, constraints, and exclusions so the implementation promise is bounded.
6. Check that core design decisions are present at planning depth without demanding the completed architecture deliverable early.
7. Apply every gate in the criteria reference with a precise evidence pointer.

## Required output

Write in the user's language unless asked otherwise. Use this order:

1. `Checkpoint result: Sufficient` or `Checkpoint result: Insufficient`.
2. `Deadline status:` including the applicable deadline and evidence.
3. `Evidence reviewed:` artifact names, versions, dates, and any missing context.
4. `Mandatory gates:` table with `ID`, `Criterion`, `Status`, `Evidence`, and `Finding`; Status is one of `Pass`, `Fail`, `Unverified`, `N/A`.
5. `Required corrections:` prioritize blockers. Each item must identify the defect, why it blocks the checkpoint, an exact repair, and passing recheck evidence. If sufficient, write `None for this checkpoint`.
6. `Comments and suggestions:` useful but non-blocking improvements, including later design/testing readiness.
7. `Scope note:` checkpoint sufficiency only; no consultation-course or final thesis grade.

Use page, requirement, use-case, story, table, or section identifiers. Avoid generic requests for "more detail". State exactly which actor, branch, acceptance condition, constraint, or trace link is missing.
