---
name: elte-bsc-audit-topic-plan
description: "Audit ELTE Faculty of Informatics BSc thesis consultation checkpoint 1: thesis topic registration, concise proposal, and work plan. Use when a student or supervisor needs a binary Sufficient/Insufficient review of a topic form, proposal, schedule, or first consultation package. Do not use for requirements, architecture, implementation, completed-thesis review, or 30-point final grading."
---

# ELTE IK BSc checkpoint 1 audit

Evaluate whether the submitted topic-registration package is sufficient for the first official BSc consultation checkpoint. Produce a strict, evidence-based decision and corrections the student can act on.

## Required references

Read both files completely before evaluating:

- [references/checkpoint-criteria.md](references/checkpoint-criteria.md) for the mandatory gates.
- [references/source-policy.md](references/source-policy.md) for source precedence, dates, and the boundary between checkpoint review and thesis grading.

When internet access is available, check the linked official deadline PDF and Gregory Morse's BSc Thesis Workflow Guidance for material changes. Treat the bundled references as a verified snapshot, not permission to import requirements from unrelated sources.

## Evidence intake

Seek the thesis topic registration form or its completed fields, the 300-500 word proposal, and the work plan. Also record the intended final-exam session, target semester, submission date, and any supervisor-approved exception. A plain statement from the student or supervisor may establish administrative facts; do not demand a screenshot unless authenticity is disputed.

Inspect every supplied artifact. Render PDF or Word files when layout affects the result. Preserve the student's files and do not rewrite or edit them unless explicitly asked.

If a mandatory artifact or fact is missing, mark the relevant gate `Unverified`. Do not infer that an unobserved item exists. An `Unverified` mandatory gate makes the result `Insufficient`.

## Decision rule

Use exactly one checkpoint result:

- `Sufficient` only when every applicable mandatory gate is `Pass` or a justified `N/A`.
- `Insufficient` when any mandatory gate is `Fail` or `Unverified`.

Use `N/A` only for a genuinely inapplicable conditional requirement and explain why. Do not waive the official work plan, concrete scope, three contributions, or registration-data gates.

Assess content sufficiency separately from timeliness. Report deadline status as `On time`, `Late`, or `Not assessed`. Lateness affects consultation-course process quality but does not turn this audit into the official Excellent/Satisfactory/Fail course grade.

Do not assign points, predict the final thesis grade, or assess later-stage completeness. Use later thesis criteria only to catch a topic that is already incapable of producing an assessable BSc thesis.

## Audit method

1. Establish the registered promise: problem, intended system, exactly three headline technical contributions, deliverables, constraints, and evidence of completion.
2. Trace each contribution to an observable acceptance signal. Reject labels that merely rename broad goals or split one trivial feature into several bullets.
3. Test judgeability, thesis-level difficulty, feasibility, and internal consistency. For UI-centered software, check the stated meaningful-code expectation; for another project type, require a comparable and explicit complexity justification.
4. Verify Gregory Morse's registration metadata character-for-character.
5. Verify that the work plan covers the five official milestones, names concrete outputs, and records the next meeting and progress due by then.
6. Apply every gate in the criteria reference and record a precise evidence pointer.

## Required output

Write in the user's language unless asked otherwise. Use this order:

1. `Checkpoint result: Sufficient` or `Checkpoint result: Insufficient`.
2. `Deadline status:` with the applicable deadline and the evidence used.
3. `Evidence reviewed:` a compact list of artifacts and versions/dates.
4. `Mandatory gates:` a table with columns `ID`, `Criterion`, `Status`, `Evidence`, and `Finding`. Use only `Pass`, `Fail`, `Unverified`, or `N/A` in Status.
5. `Required corrections:` prioritized, addressable items. For each, state what is wrong or missing, why it blocks the checkpoint, the exact repair, and what evidence would pass recheck. If sufficient, write `None for this checkpoint`.
6. `Comments and suggestions:` non-blocking improvements, clearly separated from required corrections.
7. `Scope note:` state that this is checkpoint sufficiency, not the consultation-course grade or final 30-point thesis assessment.

Keep criticism specific. Point to a page, field, paragraph, heading, table, or proposal sentence whenever possible. Do not say merely "add detail"; name the missing decision, acceptance condition, artifact, or schedule entry.
