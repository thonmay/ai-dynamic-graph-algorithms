# Difficulty, contribution, and propagation

## C1.1 Thesis-level difficulty and exam topics

Award only when both are established:

1. the student-authored task is beyond a routine compulsory-course exercise and/or has non-trivial system complexity in scope, integration, data, constraints, or environment; and
2. exactly three registered exam topics are mapped down to their relevant subtopics with authentic thesis-specific evidence.

The supervisor guidance treats the approved topic as a promise, requires at least three complex features, and gives a UI-centered target of roughly 2,000-3,000 meaningful student-authored lines excluding generated code, boilerplate, and dependencies. Treat that line target as a contextual supervisor signal for UI-centered projects, not a universal faculty threshold or a substitute for complexity.

Reject generic textbook paragraphs, dependency features, copied tutorials, configuration volume, model-generated bulk, or inflated file counts as difficulty evidence. Consider constraints, algorithmic decisions, data scale, platform boundaries, research uncertainty, and engineering trade-offs.

For exam-topic evidence, consult only the three matching sections of `03-exam-topic-evidence.md`. Verify the registered subtopics against the current official final-exam list. The topic relationship should be visible naturally in design, implementation, code, or tests; do not require headings that advertise “Exam Topic 1.”

## C1.2 Non-trivial algorithm or approach

Require a real project contribution with:

- problem and alternatives;
- chosen algorithm/approach and why;
- key trade-offs, assumptions, constraints, and complexity/correctness considerations;
- appropriate citations;
- a traceable implementation path in student-authored code;
- tests or other validation of the claimed behavior.

A standard library call can still support a point only when selection, adaptation, integration, and validation are themselves non-trivial and well explained. Merely naming an algorithm is insufficient.

## C1.3 Integration contribution

Require non-trivial coordination across components, tools, platforms, processes, or an equivalent boundary: API contracts, authentication, deployment, interoperability, frontend/backend/persistence, device/service interaction, format conversion, or a multi-stage scientific/ML pipeline.

Inspect interface contracts, failure handling, configuration, data transformations, security boundaries, and integration tests. A single trivial import or default framework wiring is insufficient.

## C1.4 Data, persistence, or larger-system context

Require a substantial data/persistence or environmental contribution appropriate to the project: schema and constraints, stored procedures, migrations, large datasets, external services, file/cloud persistence, deployment environment, protocol ecosystem, hardware context, or a larger system that had to be studied.

For a project where conventional persistence is genuinely inapplicable, test the larger-system/environment alternative. Do not award the point merely because a database was unnecessary.

## Difficulty propagation

Difficulty “underlies” later scoring through evidence, not a mechanical multiplier. When C1 loses a point, trace the factual cause through the matrix:

| Underlying fact | Possible independent consequences |
|---|---|
| Promised complex feature absent | C1 contribution; C3 workflow; C4 design; C5 plan fidelity; C6 coverage; C7 accuracy |
| Algorithm only claimed, not implemented | C1.2; C5.2; C5.3 where relevant; C6.1-C6.4; C7.1 |
| Integration is trivial or missing | C1.3; C4.1/C4.4; C5.2; C6.2; C7.1/C7.2 |
| Data scale is fabricated or untested | C1.4; C6.3; C7.3 |
| Exam topic is generic or forced | C1.1; relevant C4-C6 item only if its own required evidence is missing |

For each propagated zero, write a separate criterion-specific rationale and pointer. Do not deduct a later point solely because C1 was low. Conversely, do not let polished documentation or a live UI compensate for a trivial or undelivered task.

## C1 report block

For each C1 point, report:

- claimed contribution;
- student-authored evidence and ownership boundary;
- proposal/exam-topic trace;
- technical depth;
- contradictory evidence;
- decision and smallest addressable repair.

End with a one-paragraph difficulty judgment that distinguishes project scope, implementation depth, and documentation quality.
