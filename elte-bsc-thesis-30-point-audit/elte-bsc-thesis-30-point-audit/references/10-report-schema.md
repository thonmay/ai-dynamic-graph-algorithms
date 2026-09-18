# Audit report schema

Produce a self-contained report in this order.

## 1 Audit state and headline

State one:

- `Complete`: all thirty items resolved and all integrity gates cleared;
- `Provisional - demo pending`: documentary/code audit complete but one or more C7 items await observation;
- `Blocked - missing or unreconciled evidence`: a core artifact or integrity gate prevents a defensible score.

Then state confirmed points, lost points, pending/unverified count, possible range, zero-category status, and recommendation status.

## 2 Source and artifact ledger

List authoritative source versions/retrieval dates, all artifacts, hashes/revisions, source format, build/render result, and source/PDF parity classification. Identify every missing item as `submission absent` or `not supplied to auditor`.

## 3 Promise and evidence matrix

Include every proposal promise, complex feature, exam-topic subtopic, major requirement, and approved change. Keep evidence pointers concise but exact. Flag contradictions and all affected rubric IDs.

## 4 Point-by-point scorecard

Use exactly thirty rows:

| ID | Point test | Decision | Evidence | Material finding | Addressable correction |
|---|---|---|---|---|---|

Use only `Awarded (1)`, `Lost (0)`, `Pending demo`, or `Unverified input`. For every loss, identify the failed essential clause. For every award, provide direct evidence rather than praise.

## 5 Criterion totals

| Criterion | Awarded | Lost | Open | Status |
|---|---:|---:|---:|---|

If all items resolve, show raw subtotal, zero-category calculation, official total, and official grade band. If open items remain, show the possible range and the exact decisions needed to reach each boundary. Do not collapse a provisional range to a guessed score.

## 6 Propagated findings

Group repeated consequences by underlying defect. For each consequence, explain why the same fact independently fails the later criterion. This makes cross-category losses auditable and prevents arbitrary double counting.

Add a short **Process evidence** subsection listing checkpoint/deadline/communication facts and which, if any, existing rubric decisions they directly support. Mark any further process-based adjustment `Supervisor decision required` rather than silently changing the total.

## 7 Required corrections

Separate:

1. **Integrity/eligibility blockers** - must be resolved before a final recommendation;
2. **Score-changing corrections** - ordered by affected points and dependency order;
3. **Verification requests** - exact missing artifact or observation needed;
4. **Non-scoring suggestions** - worthwhile improvements that do not currently change a point.

Give each item an owner, artifact/location, action, acceptance check, and affected rubric IDs. Do not promise that a correction earns a point until re-audited.

## 8 PDF appearance appendix

Report page-size/margin findings, page-by-page visual defects, headings/numbering/TOC/caption issues, font/render problems, figure/table/code/equation legibility, and flagged pages inspected at high resolution. If an exact formal margin value was unavailable, say so and report measurements/consistency instead of inventing a threshold.

## 9 Code and test appendix

Record revision, ownership/exclusion boundaries, architecture/code mapping, commands/checks run, environment, failures/skips, and high-risk files/functions/tests. Never reproduce secrets.

## 10 Manual execution sheet

Include the tailored `C7.1`-`C7.6` rows from the execution reference, even when pre-demo evidence already caused a zero. The sheet should allow the supervisor to record observations without rerunning the documentary audit.

## 11 Recommendation and limitations

Use:

- `Recommend support` only when the exact official score is passing, no criterion is zero, and no integrity/eligibility blocker remains;
- `Recommend do not support` when established evidence makes support impossible under the applicable rules;
- `Supervisor decision required` when demo, policy, integrity, or missing evidence remains unresolved.

State what was not executed or independently verified. Never sign or impersonate the supervisor.

## Revision audit

When a corrected package arrives, preserve prior item IDs and decisions. Recheck changed artifacts, all dependent parity/traceability edges, and every claimed repaired point. Provide a decision delta table: `ID`, `previous`, `current`, `new evidence`, `reason`.
