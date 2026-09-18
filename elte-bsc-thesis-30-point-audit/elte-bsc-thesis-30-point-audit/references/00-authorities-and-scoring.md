# Authorities and scoring

## Source order

Apply these sources together and identify each rule's provenance:

1. **Current official ELTE rules and policies** control eligibility, submission, academic integrity, and any formal requirements they address.
2. **Updated point-by-point review form** controls the thirty scored items and the zero-category rule.
3. **Official ELTE BSc assessment guide** supplies flexible interpretation and grade bands.
4. **Gregory Morse's current BSc Thesis Workflow Guidance** supplies supervisor-specific evidence, process, length, bibliography, exam-topic, documentation, and demo requirements where it does not conflict with official rules.
5. **Approved proposal and written scope changes** control the project-specific promise.

Do not blend a supervisor requirement into an official faculty claim. Label it.

## Canonical links and checked fingerprints

- Updated point-by-point form: `https://grm.web.elte.hu/supervision/thesis_review_point_by_point_updated.docx`
  - checked 2026-09-10; SHA-256 `0ac7c6a9276d45888026b24bbfa682e81e1bc785eefdffe155ca5b435dff5fdf`
- Official assessment guide: `https://www.inf.elte.hu/dstore/document/227115/thesis_assessment.docx`
  - checked 2026-09-10; SHA-256 `dee1d3b32c1e8af288aa52573b41b26e9c0f3fc7b62f13b34a3bf3371a264136`
- Supervisor guidance: `https://grm.web.elte.hu/`, section **Supervision > BSc Thesis Workflow Guidance**
- Official BSc guidelines and current AI-policy links: follow the current links from the official ELTE or supervisor pages rather than freezing an old semester's policy.

If a live file's fingerprint differs, re-extract and visually inspect it, report the drift, and follow the current authoritative wording. If it cannot be checked, disclose that the bundled interpretation was last verified on 2026-09-10.

## Thirty binary points

The updated review form decomposes the maximum as:

| Criterion | IDs | Maximum |
|---|---|---:|
| Difficulty | C1.1-C1.4 | 4 |
| Structure, language, appearance | C2.1-C2.4 | 4 |
| User documentation | C3.1-C3.4 | 4 |
| Solution plan | C4.1-C4.4 | 4 |
| Realization | C5.1-C5.4 | 4 |
| Testing | C6.1-C6.4 | 4 |
| Program execution | C7.1-C7.6 | 6 |

Use no half-points. Award one only when all essential clauses of that item have direct, consistent evidence. A material failure in one essential clause loses that point.

## Decision states

- `Awarded (1)`: sufficient direct evidence supports every essential clause.
- `Lost (0)`: a material defect or intended-submission omission is established.
- `Pending demo`: only direct execution evidence can resolve the item and that observation has not happened.
- `Unverified input`: an audit artifact was not supplied or cannot be reconciled, but it is unknown whether the student's intended submission lacks it.

Only `Awarded` and `Lost` are final score values. Never convert `Unverified input` to `Lost` without establishing submission absence.

## Totals and grade bands

Calculate:

- `confirmed = count(Awarded)`;
- `lost = count(Lost)`;
- `open = count(Pending demo or Unverified input)`;
- `range = confirmed .. confirmed + open`.

When `open = 0`, report the raw total out of 30. If any criterion total is 0, report the official total as 0 and show the raw subtotal separately for diagnosis.

Official guide bands:

- 0-14: unsatisfactory (fail)
- 15-18: satisfactory (pass)
- 19-22: average
- 23-26: good
- 27-30: excellent

Do not assign a single band to a provisional range. Show every band the range spans and the exact conditions that determine it.

## Eligibility and integrity gates

Keep non-numeric gates separate from the thirty points. Current supervisor guidance requires a signed AI-use declaration as a separate submission file and says a missing, contradictory, or false declaration prevents evaluation. Verify the current official faculty policy for the student's semester before applying this gate.

Also record unresolved source/PDF mismatch, missing proposal, inaccessible code revision, or unverified submission identity as audit blockers. A blocker prevents a final recommendation; it is not an invented extra deduction.

## Supervisor process guidance

The current supervisor page says process quality—deadlines, checkpoints, and consistent communication—distinguishes otherwise equivalent work. Collect that history and report it. Because the updated thirty-point form has no separate process row, do not create a hidden extra point or flat penalty. Use process records only when they are direct evidence for an existing item (for example ownership, milestone authenticity, testing history, or an approved scope change), and flag any additional process-based score adjustment as an explicit supervisor decision.

Record the supplied Turnitin/pre-check status without attempting to reproduce the official service or interpreting a similarity percentage as misconduct by itself.
