---
name: elte-bsc-audit-architecture
description: "Audit ELTE Faculty of Informatics BSc thesis consultation checkpoint 3: software architecture, business rules, mandatory class diagram, and design documentation. Use when a student or supervisor needs a binary Sufficient/Insufficient review of architecture views, UML, data design, UI or API design, or requirement-to-design traceability. Do not use for other checkpoints or 30-point final grading."
---

# ELTE IK BSc checkpoint 3 audit

Evaluate whether the architecture and design package is sufficient for the third official BSc consultation checkpoint and mature enough to guide implementation.

## Required references

Read both files completely before evaluating:

- [references/checkpoint-criteria.md](references/checkpoint-criteria.md) for the mandatory design gates.
- [references/source-policy.md](references/source-policy.md) for source precedence, dates, exam-topic transition handling, and the grading boundary.

When selected final-exam topics are supplied, also read [references/exam-topic-routing.md](references/exam-topic-routing.md). When internet access is available, refresh the official deadline PDF and Gregory Morse's BSc Thesis Workflow Guidance. Do not import generic architecture requirements as ELTE gates.

## Evidence intake

Seek the design document, diagrams in legible form, approved proposal, requirements specification, planned or registered final-exam topics, and confirmation of Thesis Consultation subject registration. Record the target final-exam session, semester, submission date, and approved exceptions.

Inspect every page and diagram visually. Text extraction alone cannot establish whether a class diagram, ERD, mockup, or navigation map is readable or internally consistent. Preserve the artifacts; do not edit them unless explicitly asked.

Missing evidence is `Unverified`. Any mandatory `Fail` or `Unverified` produces `Insufficient`.

## Decision rule

- `Sufficient`: all applicable mandatory gates are `Pass` or a justified `N/A`.
- `Insufficient`: any mandatory gate is `Fail` or `Unverified`.

The official class diagram is mandatory unless the supervisor has explicitly approved an alternative for a non-class-based project. Domain-dependent views may be `N/A` only with a concrete rationale and an equivalent interaction/data explanation where needed.

Report timeliness separately. Do not assign points or the consultation-course grade. Use the final thesis rubric only to identify a design defect that would leave the later design category unassessable.

## Audit method

1. Verify substantive design volume and figure quality, excluding cover, contents, and non-design padding.
2. Check the architecture view, subsystem/layer responsibilities, interfaces, data flows, deployment assumptions, standards/technologies/methods, and separation of concerns.
3. Check explicit business rules and the mandatory class diagram against requirements and named system responsibilities.
4. Apply conditional data, UI, CLI, API, navigation, event-handler/request, and scientific-core gates according to the actual project.
5. Trace every major requirement and each of the three approved contributions into the design; flag orphan requirements and decorative components.
6. Check that design stays at design level. Low-level code and library inventory cannot substitute for architecture rationale.
7. Apply the correct semester rule to the three final-exam topics and use the topic-routing reference to judge natural, thesis-specific planned coverage.
8. Apply every gate with a precise evidence pointer and cross-document consistency check.

## Required output

Write in the user's language unless asked otherwise. Use this order:

1. `Checkpoint result: Sufficient` or `Checkpoint result: Insufficient`.
2. `Deadline status:` with deadline and evidence.
3. `Evidence reviewed:` artifact names, versions, dates, and unavailable items.
4. `Mandatory gates:` table with `ID`, `Criterion`, `Status`, `Evidence`, `Finding`; use `Pass`, `Fail`, `Unverified`, or `N/A` only.
5. `Required corrections:` prioritized blockers with defect, consequence, exact repair, and passing recheck evidence. If sufficient, write `None for this checkpoint`.
6. `Comments and suggestions:` non-blocking design improvements and later implementation risks.
7. `Scope note:` checkpoint sufficiency only; no course grade or 30-point thesis grade.

Point to diagram labels, page numbers, class/module names, interfaces, requirements, or figure numbers. For contradictions, cite both sides. Never accept a diagram because it exists; check semantics, correspondence, and legibility.
