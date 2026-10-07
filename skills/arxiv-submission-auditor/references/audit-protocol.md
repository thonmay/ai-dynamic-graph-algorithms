# Audit protocol

## Contents

1. Evidence, provenance, and severity
2. Citation verification
3. Category and classification selection
4. Canonical TeX metadata
5. Source and PDF audit
6. Deliverables and final report

## 1. Evidence, provenance, and severity

Give every finding one basis: `ARXIV POLICY`, `STRICT PUBLICATION DEFAULT`, or `GREGORY PREFERENCE`. State stricter layers separately when an official minimum and local default differ.

- **BLOCKER**: submission would fail, misrepresent facts, violate policy, rely on an unavailable artifact, contain an unverified/unsupported citation, omit required disclosure, or ship incomplete/inconsistent source.
- **WARNING**: meaningful quality, discoverability, portability, reproducibility, or moderation risk.
- **NOTE**: verified fact or optional improvement.

For every finding record an identifier, basis, severity, file/location, evidence, exact correction, and whether author confirmation is required. Never turn missing evidence into a pass.

## 2. Citation verification

Audit both every bibliographic work and every in-text occurrence.

### Work-level ledger

| Field | Required evidence |
| --- | --- |
| Identity | Primary paper/book/standard or official publisher/DOI/arXiv record |
| Metadata | Exact authors, title, venue, year, volume/issue, pages or article number |
| Persistent IDs | DOI, arXiv ID/version, ISBN, standard number, or other stable ID |
| Status | Preprint/published relationship, relevant version, erratum/correction/retraction status |
| Source access | URL opened and access date; inaccessible full text is unresolved |
| Bib consistency | TeX/BibTeX entry matches the verified work and citation style |
| Result | `VERIFIED`, `PARTIAL`, or `BLOCKER` with reason |

Use primary technical sources. Search results, snippets, aggregators, or another bibliography may locate a source but do not verify it.

### Occurrence-level ledger

For each `\cite...` occurrence record the key(s), nearby statement, attributed relationship, and supporting theorem/section/page/equation when available. Confirm the source supports the claim with its actual hypotheses and scope. Separately verify priority language such as `first`, `classical`, `best known`, or `independently`. Mark inaccessible text, ambiguous attribution, metadata conflicts, unsupported claims, or retraction concerns as blockers.

Also check missing/duplicate keys, uncited entries, malformed identifiers, secondary-source attribution, and bibliography/package consistency.

Apply the field-level and two-build-path bibliography protocol in `packaging-and-bibliography.md`. Do not describe the strict `.bib` + `.bbl` default as an arXiv requirement.

## 3. Category and classification selection

1. Extract the central result, methods, objects, intended expert audience, and closest literature.
2. Compare them with live arXiv taxonomy descriptions.
3. Inspect several recent accepted papers with genuinely similar central contributions; use them only as calibration.
4. Recommend exactly one primary subject and only substantial cross-lists.
5. Verify every official label and code. Record rejected plausible categories and why.

Use this exact human-readable syntax in the TeX metadata region:

```text
Subjects: Data Structures and Algorithms (cs.DS)
MSC classes: 68Q25 (Primary) 68N20, 05C85 (Secondary)
ACM classes: F.2.2; D.3.4; F.3.2
```

List the primary arXiv subject first; append justified cross-lists with `; `. Keep both classification lines in the TeX record. Use `N/A -- leave blank` when MSC or ACM classification is genuinely inapplicable so the audit decision remains explicit; leave the corresponding arXiv web field blank.

Map the TeX record to arXiv's web form exactly:

| TeX record | arXiv web form action |
| --- | --- |
| `Comments: <value>` | Paste `<value>` into `Comments` |
| `Subjects: Label (code); ...` | Select the first code as the primary `Category` and the rest as cross-lists |
| `MSC classes: <value>` | Paste `<value>` into `MSC-class` |
| `ACM classes: <value>` | Paste `<value>` into `ACM-class` |

The plural human-readable labels are the self-contained TeX record; the singular hyphenated labels are arXiv's form field names. Do not paste the label itself into the field.

## 4. Canonical TeX metadata

Place one raw false-conditional region immediately before `\begin{document}` unless the source structure requires another safe location. Do not prefix lines with `%`. Use ASCII paste values and compile-test the exact source.

For the common case in which the visible abstract is already directly pasteable, use:

```tex
\iffalse
ARXIV-METADATA-BEGIN
Title: <exact paste value>
Authors: <exact paste value>
Abstract source: copy abstract environment verbatim
Comments: 11 pages, 3 tables, 3 algorithms
Subjects: Data Structures and Algorithms (cs.DS)
MSC classes: 68Q25 (Primary) 68N20, 05C85 (Secondary)
ACM classes: F.2.2; D.3.4; F.3.2
Report number: N/A -- leave blank
Journal reference: N/A -- leave blank
DOI: N/A -- leave blank
License: <confirmed selection>
Submitter is author: Yes
External artifacts: GitHub <exact public URL>; release/tag <value>; commit <hash>; verified <date>
AI disclosure: <visible section name> -- <exact visible disclosure text>
ARXIV-METADATA-END
\fi
```

If the visible abstract is not directly pasteable, replace the `Abstract source:` line with one physical line:

```text
Abstract: <complete expanded paste value>
```

Use exactly one of `Abstract:` or `Abstract source:`:

- Use `Abstract source: copy abstract environment verbatim` only after confirming the abstract body itself is ASCII-safe, no more than the live limit, directly pasteable without its environment delimiters, and free of opaque/local macros, unsupported formatting, citations, labels, spacing commands, or TeX-only special-character issues.
- Otherwise put the complete transformed arXiv value after `Abstract:`. Keep it scientifically identical to the visible abstract, expand only what arXiv needs, and put the full value on one physical line.

The visible abstract remains authoritative scientifically; the audit must compare it with the paste value and block semantic divergence. If a duplicate expanded value is unnecessary, avoid it rather than creating two maintenance points.

Build `Comments` from the final rendered manuscript, counting pages and every present object type worth reporting: figures, tables, and algorithms. Add a concise public artifact URL when one exists, for example: `Comments: 11 pages, 3 tables, 3 algorithms. Code and certificates: https://github.com/OWNER/REPO`.

The false region is the canonical submission checklist. `ARXIV_METADATA.txt` may be derived from it for convenience but must not replace it.

## 5. Source and PDF audit

Check:

- one unambiguous main file and intended engine;
- recursively complete TeX, figure, bibliography, style/class/font, index/glossary, and ancillary dependencies;
- legal filenames, exact case, and no local absolute paths;
- current bibliography processing and matching main-file `.bbl` when used;
- separate `.tex`, `.bib`, and `.bbl` key sets; recorded bibliography package/style/backend/tool versions; byte-identical regenerated and shipped `.bbl`;
- no stale build output, journal-only bundles, secrets, private referee files, or unrelated artifacts;
- clean compilation with zero unresolved citations/references, missing glyphs/files, or unexplained warnings;
- correct rendering of title, authors, affiliations, abstract, acknowledgments, artifact URLs, references, figures, tables, algorithms, appendices, page count, and rights text;
- no line numbers, referee mode, highlighted edits, margin notes, hidden prompts/text, obstructive watermarks, advertisements, or incompatible redistribution language;
- selectable/machine-readable PDF text and legible figures.
- final ZIP built from an explicit allowlist, extracted safely, and compiled without BibTeX/Biber; no code/artifact or administration files under the strict default;
- exact final archive manifest, one current upload ZIP, verified recursive SHA-256 checksums, and metadata/counts regenerated after the final change.

Inspect the rendered PDF; a zero compiler exit code is insufficient.

## 6. Deliverables and final report

Create:

- the synchronized `\iffalse` metadata region in the main TeX source;
- `ARXIV_AUDIT.md` outside the upload source;
- optional `ARXIV_METADATA.txt` derived from the TeX region;
- a clean upload archive only after every hard gate passes.

Structure `ARXIV_AUDIT.md` as:

1. Final status and one-sentence reason
2. Blockers
3. Requirement provenance (`ARXIV POLICY`, `STRICT PUBLICATION DEFAULT`, `GREGORY PREFERENCE`)
4. Required author confirmations
5. Canonical TeX metadata validation
6. Category/classification decision and rejected alternatives
7. Novelty, prior-open-status, model, and exact-frontier ledger
8. Citation work-level and BibTeX-field ledger
9. Citation occurrence-level ledger
10. External-artifact manifest and live verification
11. Final ZIP allowlist/manifest and two-path bibliography/compiler audit
12. Rendered-PDF and regression audit
13. Authorship, affiliation, AI disclosure, rights, and separated licenses
14. Checksums and post-final-change revalidation
15. Exact edits made
16. Official policy sources with access dates

End with only actions still requiring the author or arXiv web interface. Do not use `SUBMISSION-READY` until every blocker is closed.
