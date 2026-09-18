---
name: elte-bsc-audit-final-thesis
description: "Audit ELTE Faculty of Informatics BSc thesis consultation checkpoint 5: presentation of the completed thesis and submission readiness. Use when a student or supervisor needs a binary Sufficient/Insufficient preflight of the final thesis PDF, source, running software, documentation, tests, approved commitments, exam-topic integration, AI declaration, and submission package. Do not use to assign the later 30-point thesis score or grade."
---

# ELTE IK BSc checkpoint 5 audit

Evaluate whether the completed thesis is ready for supervisor presentation, upload, and final-exam processing. The official checkpoint is not part of fulfillment of the Thesis Consultation subject, but it is necessary for thesis upload and the final examination.

## Required references

Read all three files completely before evaluating:

- [references/checkpoint-criteria.md](references/checkpoint-criteria.md) for mandatory readiness gates.
- [references/final-quality-calibration.md](references/final-quality-calibration.md) for the seven thesis areas that must remain minimally assessable without assigning points.
- [references/source-policy.md](references/source-policy.md) for source precedence, dates, AI and submission boundaries, and safe execution.

When selected final-exam topics are supplied, also read [references/exam-topic-routing.md](references/exam-topic-routing.md). When internet access is available, refresh the official deadline PDF and Gregory Morse's BSc Thesis Workflow Guidance.

## Evidence intake

Seek the final thesis PDF, approved proposal form, complete source archive or repository at a fixed revision, reproducible setup/run instructions, dependency/environment manifests, test artifacts, running demonstration, exactly three registered final-exam topics and subtopics, and the signed AI declaration when AI was used or the current policy requires it. Record semester, final-exam session, submission date, approved scope changes, and the intended Neptun or deferred-submission route.

Render and inspect every thesis page. Inspect figures, tables, cross-references, bibliography, and inserted proposal visually. Compare source, documented behavior, and demonstrated revision. Run only safe local tests; do not access production services, credentials, paid resources, or mutable external data.

An absent or unverifiable mandatory item is `Unverified`, which makes the result `Insufficient`. Do not infer authorship from style, use an AI detector, or treat a Turnitin percentage as proof of misconduct. Audit declarations, citations, point-of-use disclosure, and technical verification evidence instead.

## Decision rule

- `Sufficient`: every applicable mandatory gate is `Pass` or a justified `N/A`, and every one of the seven final quality areas has enough evidence to be assessable above zero.
- `Insufficient`: any mandatory gate is `Fail` or `Unverified`, or any final quality area is effectively absent/unassessable.

Do not assign the 30-point score, recommend a numerical grade, or decide formal support for defense. The later assessment is deliberately separate. Page-count minima stated by the supervisor are gates; the typical 60-70 total pages and the 70-80-page high-grade observation are guidance, not automatic pass/fail thresholds.

Report timeliness separately. A mock defense 1-2 weeks before the final examination is recommended, not a checkpoint pass gate unless separately required for the cohort.

## Audit method

1. Reconcile the final system and thesis against the approved topic promise, exactly three contributions, requirements, design, and approved scope changes.
2. Verify all compulsory front matter, user and developer documentation, bibliography, contents, appendix/run instructions, and separate AI declaration/package elements.
3. Verify supervisor page minima and substantive content, not page inflation.
4. Audit the seven final quality areas using the calibration reference. Treat a crash under ordinary ethical testing as a blocker.
5. Trace each complex contribution through requirement, design, implementation, user documentation, tests, and demonstration.
6. Privately map all three registered final-exam topics and their listed subtopics to substantive thesis-specific passages and implementation evidence. The thesis itself should not read like an exam-topic checklist.
7. Verify citation/quotation integrity, actual installation/run correspondence, source-to-demo identity, limitations, reproducibility, and AI-use consistency.
8. Apply every readiness gate with precise evidence pointers.

## Required output

Write in the user's language unless asked otherwise. Use this order:

1. `Checkpoint result: Sufficient` or `Checkpoint result: Insufficient`.
2. `Submission route and deadline status:` route, applicable deadline, and evidence.
3. `Evidence reviewed:` thesis revision, source revision, demo/test evidence, declarations, and unavailable items.
4. `Mandatory gates:` table with `ID`, `Criterion`, `Status`, `Evidence`, `Finding`; use `Pass`, `Fail`, `Unverified`, or `N/A` only.
5. `Seven-area zero-risk check:` compact table naming each final assessment area and whether it is minimally assessable. Do not give points.
6. `Required corrections:` prioritized blockers; for each give defect, consequence, exact repair, and passing recheck evidence. If sufficient, write `None for this checkpoint`.
7. `Comments and suggestions:` non-blocking quality improvements and defense-preparation advice.
8. `Scope note:` checkpoint-five submission readiness only; no official support decision, 30-point score, or thesis grade.

Use page/section/figure/table numbers, bibliography entries, file paths, commit IDs, test names, and demo steps. For cross-artifact inconsistency, cite both locations. Do not accept declarations, diagrams, tests, or setup instructions merely because they exist; verify correspondence.
