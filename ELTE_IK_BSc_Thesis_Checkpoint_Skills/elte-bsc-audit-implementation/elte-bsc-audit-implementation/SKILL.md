---
name: elte-bsc-audit-implementation
description: "Audit ELTE Faculty of Informatics BSc thesis consultation checkpoint 4: presentation of a genuinely runnable 60-70 percent implementation. Use when a student or supervisor needs a binary Sufficient/Insufficient review of code, repository history, live or recorded demonstration, debugging, implementation documentation, testing evidence, and progress against approved commitments. Do not use for final grading or another checkpoint."
---

# ELTE IK BSc checkpoint 4 audit

Evaluate whether the demonstrated implementation has reached the official 60-70 percent milestone and is supported by credible engineering evidence. This is the last consultation milestone used for entering the Thesis Consultation grade, but this skill does not assign that grade.

## Required references

Read both files completely before evaluating:

- [references/checkpoint-criteria.md](references/checkpoint-criteria.md) for the mandatory implementation gates and completion calculation.
- [references/source-policy.md](references/source-policy.md) for source precedence, dates, safe execution, and the grading boundary.

When selected final-exam topics are supplied, also read [references/exam-topic-routing.md](references/exam-topic-routing.md). When internet access is available, refresh the official deadline PDF and Gregory Morse's BSc Thesis Workflow Guidance.

## Evidence intake

Seek the approved proposal, requirements, design, current repository or source archive, commit history, runnable setup instructions, implementation-documentation draft, tests/results, and live demonstration or sufficiently direct recording. Record the semester, final-exam session, submission/demo date, selected topics, and approved scope changes.

Do not count files, commits, generated code, boilerplate, mocked screens, dead code, scaffolding, or isolated snippets as completed functionality. Do not execute untrusted binaries or commands that access production services, credentials, paid resources, or external mutable data. Ask for a safe local/test configuration when needed.

If direct execution or demo evidence for the core paths is unavailable, mark those gates `Unverified`; a polished repository is not a substitute. Any mandatory `Fail` or `Unverified` produces `Insufficient`.

## Decision rule

- `Sufficient`: all mandatory gates pass and the evidence-supported completion ratio is at least 60 percent.
- `Insufficient`: any mandatory gate fails or is unverified, or supported completion is below 60 percent.

Treat 70 percent as the upper description of the target milestone, not a penalty for being further ahead. Report deadline status separately. Do not assign a three-point course grade or 30-point thesis grade.

## Audit method

1. Build a commitment ledger from the approved proposal, exactly three contributions, and requirements. Incorporate documented scope changes only when supervisor approval is evidenced.
2. Weight commitments by technical effort or approved importance when evidence supports it; otherwise use transparent equal weighting and state the limitation.
3. Credit only work that is implemented, integrated, runnable in the intended path, and demonstrated or independently verifiable. Partially credit a commitment only with an explicit completed fraction and evidence.
4. Report the numerator, denominator, weighting basis, and resulting completion range. Do not use lines of code as the denominator.
5. Inspect representative core code, error handling, data representation, interfaces, design correspondence, repository evolution, reproducibility, and tests. Verify that deviations from design are recorded and justified.
6. Assess live debugging familiarity appropriate to the stack and demonstration of relevant browser, IDE, API, database, or console inspection workflows.
7. Check that final-exam topic choices have been discussed and implementation-heavy coverage is being documented naturally.
8. Apply every gate in the criteria reference with precise evidence pointers.

## Required output

Write in the user's language unless asked otherwise. Use this order:

1. `Checkpoint result: Sufficient` or `Checkpoint result: Insufficient`.
2. `Completion finding:` percentage or defensible range, numerator/denominator, and weighting method.
3. `Deadline status:` applicable deadline and evidence.
4. `Evidence reviewed:` artifacts, commit/release identifier, demo form/date, tests run, and unavailable evidence.
5. `Mandatory gates:` table with `ID`, `Criterion`, `Status`, `Evidence`, `Finding`; use `Pass`, `Fail`, `Unverified`, or `N/A` only.
6. `Required corrections:` prioritized blockers with exact repair and recheck evidence. If sufficient, write `None for this checkpoint`.
7. `Comments and suggestions:` non-blocking work toward completion and final thesis quality.
8. `Scope note:` checkpoint sufficiency only; no official course or thesis grade.

Name files, functions, commits, test cases, demo steps, requirements, and features. Distinguish observed behavior from student claims. Never describe a percentage as precise when the evidence supports only a range.
