# Intake and source-to-PDF parity

## Evidence ledger

Create a ledger before scoring:

| Artifact | Required identity | Received | Immutable identifier | Purpose | Status |
|---|---|---|---|---|---|
| Final PDF | submitted version | | hash/page count | appearance and submission state | |
| Editable source | same revision as PDF | | hash/build | substance and reproducibility | |
| Approved proposal | faculty-approved PDF | | hash/date | promised scope | |
| Scope changes | supervisor-approved | | message/date | authorized deviations | |
| Code | complete fixed revision | | commit/hash | implementation evidence | |
| Tests/data | matching code revision | | hash/run ID | test evidence | |
| Exam topics | exactly three registered topics | | form/date | C1.1 mapping | |
| AI declaration | signed applicable form | | hash/date | eligibility/integrity | |
| Checkpoint/process record | dated decisions/evidence | | dates/links | ownership, approvals, process | |
| Demo observations | supervisor record | | date/observer | C7 | |

Classify absent evidence as either `submission absent` or `not supplied to auditor`.

## Safe intake

- Preserve originals and record hashes before conversion.
- Inspect archives for path traversal, symlinks, nested archives, secrets, binaries, generated/vendor trees, and unexpectedly large files before extraction.
- Work on copies. Do not rewrite the student's source.
- Record the repository HEAD, branch/tag, submodules, dirty state, and whether history is included.
- Never expose secrets found during inspection; report file and secret type without reproducing the value.

## Editable-source rules

### LaTeX

Require the complete project: root `.tex`, included files, bibliography, images, class/style files, and build instructions. Compile in an isolated environment when safe. Record engine, warnings, missing references/citations, page count, and produced PDF hash. A build failure makes parity unverified; it does not by itself prove the submitted PDF invalid.

### Word

Require `.docx`, not only a PDF. Inspect headings/styles, fields, captions, comments, tracked changes, images, section settings, and document properties. Render to PDF and page images. Unresolved tracked changes or comments in an intended final source are reportable defects.

### Google Docs

Require a same-revision `.docx` export plus the submitted PDF. A live link or view-only URL may help identify revision history but cannot replace the local export. Record the export date/revision if available. Render the `.docx`; do not assume browser and export pagination are identical.

## Parity test

Do not demand byte equality. Compare:

1. title, author, proposal form, headings, and section order;
2. normalized paragraph text and citation markers;
3. figures, tables, captions, equations, appendices, and bibliography;
4. page count and major pagination differences;
5. revision metadata and build output;
6. visible tracked changes, comments, placeholders, or omitted source sections.

Classify differences:

- **render-only**: expected font/line/page flow differences with the same substance;
- **minor substantive**: local wording or caption mismatch that does not alter evidence;
- **material substantive**: missing/added sections, claims, figures, results, citations, proposal page, or altered conclusions;
- **unreconciled**: source cannot build/render or provenance is unknown.

A material or unreconciled mismatch blocks an exact final audit until the authoritative same-revision source is identified.

## Promise matrix

Create rows for:

- every approved deliverable and measurable proposal commitment;
- at least three promised complex features;
- every selected exam topic and registered subtopic;
- every major functional/non-functional requirement;
- every written scope change.

Use columns: `Promise`, `Source`, `Acceptance signal`, `Design evidence`, `Thesis implementation evidence`, `Code evidence`, `Test evidence`, `Demo evidence`, `Status`, `Affected rubric IDs`.

Use `Delivered`, `Partly delivered`, `Missing`, `Changed with approval`, or `Unverified`. This matrix is the backbone for propagation; never infer delivery from a thesis claim alone.

Also inventory the intended submission archive itself: final PDF, editable thesis source, complete code and artifacts, reproducibility/run README, and the currently required declaration files. Distinguish a missing archive component from a component merely stored alongside the archive when the applicable submission rules allow it.
