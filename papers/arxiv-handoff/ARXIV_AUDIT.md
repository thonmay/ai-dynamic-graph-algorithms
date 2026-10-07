# ARXIV_AUDIT.md — pre-submission audit

Manuscript: *Locality and stability of maximum cardinality search orderings under edge updates, with a machine-checked implementation*
Audit tool: `arxiv-submission-auditor` (`scripts/audit_tex.py`), run 2026-10-04.
Auditor runtime: aiserver, Python 3.11.14, TeX Live 2021 (`pdfTeX 3.141592653-2.6-1.40.22`), poppler present.

## 1. Final status

**CONDITIONALLY READY** — all machine-checkable gates pass; one accepted author deviation (`AI_MODE_MISSING`, a `STRICT PUBLICATION DEFAULT`, relaxed by explicit author decision) remains, plus two author-confirmation items (novelty ledger, and the arXiv web-form actions).

## 2. Blockers

| ID | Basis | Status |
|---|---|---|
| `AI_MODE_MISSING` | STRICT PUBLICATION DEFAULT | **Accepted deviation.** The auditor requires an exact thinking/reasoning *mode* (e.g. "high thinking mode") for every named model. The harness ground truth (`~/.enlcode/config.json`) records only `reasoning: true` (interleaved chain-of-thought) with **no effort tier** for DeepSeek-V4-Flash-0731, Claude Opus 5.5, or Qwen3.8-27B-FP8. The human author chose to disclose provider + model + role only, and to make no mode claim. This is stricter-than-required local convention, not an arXiv policy rule, so it is recorded as an explicit author decision rather than a defect. |

No other blockers.

## 3. Requirement provenance

- `ARXIV POLICY`: TeX source ships with `.bib`; abstract ASCII-safe and < 1920 chars; cs submission uses legacy ACM codes; machine-readable, single-spaced, 1-inch margins; AI use disclosed in the work.
- `STRICT PUBLICATION DEFAULT`: canonical `\iffalse` metadata region; public pinned artifact; regenerated matching `.bbl`; allowlist-only ZIP; shipping build; exact AI model/mode.
- `GREGORY PREFERENCE`: main TeX file is the canonical metadata record; publication administration kept out of the public code repository.

## 4. Required author confirmations

- [ ] Novelty ledger for the two "first" claims (Section 7) reviewed and signed off.
- [ ] arXiv web-form actions (upload, select cs.DS primary + math.CO cross-list, paste MSC/ACM, select CC BY 4.0, inspect rendered PDF, approve).
- [x] License choice: CC BY 4.0 (author-confirmed 2026-10-04).
- [x] Artifact pin: `mcs-arxiv-v2` tagged and pushed to the public repo (author-confirmed 2026-10-04).
- [~] AI reasoning mode: relaxed to provider/model/role only (author-confirmed 2026-10-04).

## 5. Canonical TeX metadata validation

One raw `\iffalse` / `\fi` region (`ARXIV-METADATA-BEGIN` … `ARXIV-METADATA-END`) sits immediately before `\begin{document}`. Compile-tested; 14 fields. `ARXIV_METADATA.txt` is derived from it byte-for-byte by stripping the markers.

- Abstract is **not** copy-paste-safe (contains `\emph`, `$P_4$`), so the region uses the expanded single-line `Abstract:` form. Scientific identity with the visible abstract confirmed (only macro/format expansion differs): `emph{}` → plain; `$P_4$` → `P_4`; `Lean~4` → `Lean 4`.
- Comments page count reconciled from the extracted final ZIP (12 pages, 1 table).

## 6. Category / classification decision

- **Primary:** Data Structures and Algorithms (`cs.DS`) — the central contribution is dynamic graph-search ordering maintenance with an algorithmic update and complexity claims.
- **Cross-list:** Combinatorics (`math.CO`) — MCS chordality, matching/star structure, and the P_4/triangle obstructions are combinatorial.
- **Rejected:** `cs.LO` / `cs.PL` (the Lean artifact is evidence, not the contribution); `math.LO` (same reason).
- **MSC:** 68Q25 (Primary) 05C85 (Secondary). **ACM:** F.2.2; G.2.2; F.3.2.

## 7. Novelty / prior-open-status ledger

Two `first` claims appear (abstract + conclusion): *first maintenance of an MCS ordering under edge updates* and *first machine-checked correctness proof of a maintained graph-search ordering*.

- Nearest prior art: Ibarra 2008 (dynamic chordal, clique-tree, not the MCS ordering); Banerjee–Raman–Satti 2018 (PEO under deletions, different window, cell-probe lower bound); Mezzini 2012 (O(1) query / O(n²) update chordal). None maintains the MCS ordering itself; none machine-checked.
- Morse–Kozsik 2026 (dynamic BFS in directed graphs) is the closest dynamic-search-ordering result; it is BFS in directed graphs, not MCS in undirected graphs, and is not machine-checked.
- Guéneau et al. 2019 is the nearest verified dynamic graph algorithm (incremental cycle detection, Coq); no MCS or PEO formalization found.
- **Residual uncertainty:** the "first" wording is qualified in the abstract with "To our knowledge". Retained. `external_verification_performed: false` — this ledger is a literature search over the paper's cited prior art, not a systematic survey; the qualified wording is the wording the evidence permits.

## 8. Citation work-level ledger

10 keys, all field-verified against primary records (Crossref / Dagstuhl DRO / arXiv API) 2026-10-04, recorded in `references.bib` header comments:

`rose1976algorithmic`, `tarjan1984mcs`, `corneil2008unified`, `berry2004mcs`, `brandstadt1997lexbfs`, `ibarra2008dynamic`, `banerjee2018maintaining`, `mezzini2012fully`, `gueneau2019formal`, `morse2026bfs`.

Zero missing keys, zero duplicate keys, zero uncited keys.

## 9. Citation occurrence-level ledger

13 `\cite` occurrences across the 10 works; each attribution checked against the source's hypotheses and scope. No retractions/corrections outstanding. The Corneil–Krueger incomparability claim and the brute-force witness (204/204, symmetric difference 40) are reproduced in the artifact README.

## 10. External-artifact manifest (live verification, 2026-10-04)

| Field | Value |
|---|---|
| Repository | https://github.com/thonmay/thesis-lean |
| Public (unauth) | HTTP 200 |
| Pin | annotated tag `mcs-arxiv-v2` (Lean proof) |
| Tag dereference (unauth `git ls-remote`) | `mcs-arxiv-v3^{}` → `afcc911405e9bb7e7ea4b9d8537d2ce2f1e731a5` |
| Commit files reachable at pin | `README.md` 200, `comparator.json` 200, `formalization.yaml` 200, `lean-toolchain` 200, `AxiomAudit.lean` 200 |
| Role | Logically required (all theorems) |
| Visible in paper | Yes (reproducibility paragraph, `sec:formalization`) |
| In Comments | Yes |
| License | Apache-2.0 (repo) vs CC BY 4.0 (arXiv manuscript) — separate, intentional |

## 11. Final ZIP allowlist, manifest, and two-path build

- Allowlist (one path per line): `main.tex`, `references.bib`, `main.bbl`.
- ZIP members (verified, `allowlist_matches: true`): `main.tex` (29753 B), `references.bib` (5723 B), `main.bbl` (3603 B). No build debris, no PDF, no code, no Lean sources, no audits.
- Full-source build (aiserver, TeX Live 2021): LaTeX → BibTeX → LaTeX ×2, exit 0, 12 pages, 0 overfull, 1 underfull.
- Shipping build (extracted ZIP, no BibTeX/Biber, 3 runs): all rc=0, 12 pages, 23470 selectable-text chars, fonts embedded, 0 overfull, 1 underfull.
- `.bbl` byte-identical: `matches_shipped_bbl: true`.
- ZIP SHA-256: `a2d57278d668d964ff129951996dd915a53c285eee3f2bc25fc05f03b7ca504c`.

## 12. Rendered-PDF audit

12 pages, letter, selectable text, fonts embedded (`pdffonts` all `emb yes`). Title, authors, affiliations, abstract, acknowledgements/CI, artifact URL, references all render. No line numbers, highlights, watermarks, or referee material. One underfull hbox (line ~237–241): **cosmetic** (a short line in a bullet list, badness 2080).

## 13. Authorship, affiliation, AI disclosure, rights

- Authors: Md Thoriqul Islam Thonmay (first), Gregory Morse. Both ELTE, Department of Programming Languages and Compilers. Author order unchanged. Submitter is the first author.
- AI disclosure: visible unnumbered section; provider + exact model ID + role for all three models; "No AI system is an author"; authors accept full responsibility. Divergence check (metadata line vs visible text) passes: the metadata field copies the visible paragraph verbatim.
- Rights: arXiv license CC BY 4.0 (author-confirmed); repository Apache-2.0; third-party deps (Lean 4, Mathlib) under their own licenses.

## 14. Checksums

`main-upload.zip` SHA-256 above; `clean-build.bbl` and the in-ZIP `main.bbl` byte-identical (3603 B). Recompute after any further change.

## 15. Exact edits made this session

1. Added the `\iffalse` metadata region before `\begin{document}`.
2. Replaced the Acknowledgements/AI section with provider + exact model ID + role wording (removed vendor-generic phrasing).
3. Added a visible `Artifact and reproducibility` paragraph with the public repo URL, tag, commit, and role distinction.
4. (Earlier) Comparator count 36 → 37; online corollary promoted from observation to `Corollary` (`common_order_extends_prefix`); contributions bullet updated.
5. Created and pushed annotated tags `mcs-arxiv-v1` (on `a872fdd`, session 1) and `mcs-arxiv-v2` (on `a92df35`, adds the public verification scripts).

## 16. Official policy sources

Bundled snapshot `references/arxiv-policy.md` (baseline 2026-08-30). Live pages to re-open at submission: https://info.arxiv.org/help/submit_tex.html, https://info.arxiv.org/help/prep.html, https://arxiv.org/category_taxonomy, https://info.arxiv.org/help/license/index.html. Access date for this audit: 2026-10-04.
