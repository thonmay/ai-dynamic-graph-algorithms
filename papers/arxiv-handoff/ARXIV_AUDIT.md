# ARXIV_AUDIT.md — pre-submission audit

Manuscript: *How rigid is maximum cardinality search? Stability and locality of MCS orderings under edge updates, verified in Lean*
Audit tool: `arxiv-submission-auditor` (`scripts/audit_tex.py`), last run 2026-10-31 (`arxiv-r3/r12.json`).
Auditor runtime: aiserver, Python 3.11.14, TeX Live 2021 (`pdfTeX 3.141592653-2.6-1.40.22`), poppler present.

## 1. Final status

**PENDING SUPERVISOR REVIEW** — 0 blockers, 4 warnings (`ABSTRACT_TRANSFORM_VERIFY`, `ARTIFACT_LIVE_VERIFY`, `NOVELTY_AUDIT_REQUIRED`, `PDF_UNDERFULL_BOX`), each classified below. Remaining before upload: the supervisor's next review round, completion of the Palomar v3 registration (consented and started; see Section 10), and the arXiv web-form actions.

## 2. Blockers

None. `AI_MODE_MISSING` is resolved: the visible disclosure now gives a thinking mode for every named model (author-confirmed 2026-10-19: Claude Opus 5.5 in high thinking mode; DeepSeek-V4-Flash-0731 and Qwen3.8-27B-FP8 with thinking mode on at default effort, since those harnesses expose no effort tier; Humanizer 12B no reasoning mode).

Warnings, classified:
- `ABSTRACT_TRANSFORM_VERIFY`: metadata abstract is the ASCII expansion of the visible one ($G\triangle F$ -> "the modified graph", `P_4`, `+1`); same claims.
- `ARTIFACT_LIVE_VERIFY`: live ledger in Section 10 (unauthenticated checks, 2026-10-19).
- `NOVELTY_AUDIT_REQUIRED`: "first" claims are hedged ("to our knowledge", survey stated in Section 8 of the paper); ledger in Section 7 of this file.
- `PDF_UNDERFULL_BOX`: one, Theorem 14 header (long Lean-name list); cosmetic.

## 3. Requirement provenance

- `ARXIV POLICY`: TeX source ships with `.bib`; abstract ASCII-safe and < 1920 chars; cs submission uses legacy ACM codes; machine-readable, single-spaced, 1-inch margins; AI use disclosed in the work.
- `STRICT PUBLICATION DEFAULT`: canonical `\iffalse` metadata region; public pinned artifact; regenerated matching `.bbl`; allowlist-only ZIP; shipping build; exact AI model/mode.
- `GREGORY PREFERENCE`: main TeX file is the canonical metadata record; publication administration kept out of the public code repository.

## 4. Required author confirmations

- [ ] Novelty ledger for the two "first" claims (Section 7) reviewed and signed off.
- [ ] arXiv web-form actions (upload, select cs.DS primary + math.CO cross-list, paste MSC/ACM, select CC BY 4.0, inspect rendered PDF, approve).
- [x] License choice: CC BY 4.0 (author-confirmed 2026-10-04).
- [x] Artifact pin: `mcs-arxiv-v7` tagged, pushed and published as a GitHub Release; Software Heritage save request accepted 2026-10-19.
- [x] AI reasoning mode per model (author-confirmed 2026-10-19).
- [x] Author contacts: emails in the title footnotes; first author marked BSc student (author-confirmed 2026-10-19). ORCIDs not provided.

## 5. Canonical TeX metadata validation

One raw `\iffalse` / `\fi` region (`ARXIV-METADATA-BEGIN` … `ARXIV-METADATA-END`) sits immediately before `\begin{document}`. Compile-tested; 14 fields. `ARXIV_METADATA.txt` is derived from it byte-for-byte by stripping the markers.

- Abstract is **not** copy-paste-safe (contains `\emph`, `$P_4$`), so the region uses the expanded single-line `Abstract:` form. Scientific identity with the visible abstract confirmed (only macro/format expansion differs): `emph{}` → plain; `$P_4$` → `P_4`; `Lean~4` → `Lean 4`.
- Comments page count reconciled from the extracted final ZIP (15 pages, 1 table).

## 6. Category / classification decision

- **Primary:** Data Structures and Algorithms (`cs.DS`) — the central contribution is dynamic graph-search ordering maintenance with an algorithmic update and complexity claims.
- **Cross-list:** Combinatorics (`math.CO`) — MCS chordality, matching/star structure, and the P_4/triangle obstructions are combinatorial. Logic in Computer Science (`cs.LO`) — the machine-checked formalization is a first-class contribution and the paper is positioned for the formal-methods readership.
- **MSC:** 68Q25 (Primary) 68V15, 68R10, 05C85 (Secondary). **ACM:** F.3.1; G.2.2; F.2.2 (F.3.1 = specifying, verifying and reasoning about programs).

## 7. Novelty / prior-open-status ledger

Two `first` claims appear (abstract + conclusion): *first locality analysis of an MCS ordering under edge updates* and *first machine-checked incremental repair of a graph-search ordering*.

- Nearest prior art: Ibarra 2008 (dynamic chordal, clique-tree, not the MCS ordering); Banerjee–Raman–Satti 2018 (PEO under deletions, different window, cell-probe lower bound); Mezzini 2012 (O(1) query / O(n²) update chordal). None maintains the MCS ordering itself; none machine-checked.
- Morse–Kozsik 2026 (dynamic BFS in directed graphs) is the closest dynamic-search-ordering result; it is BFS in directed graphs, not MCS in undirected graphs, and is not machine-checked.
- Guéneau et al. 2019 is the nearest verified dynamic graph algorithm (incremental cycle detection, Coq); no MCS or PEO formalization found.
- **Residual uncertainty:** the "first" wording is qualified in the abstract with "To our knowledge". Retained. `external_verification_performed: false` — this ledger is a literature search over the paper's cited prior art, not a systematic survey; the qualified wording is the wording the evidence permits.

## 8. Citation work-level ledger

15 keys, all field-verified against primary records (Crossref / Dagstuhl DRO / arXiv API), recorded in `references.bib` header comments:

`rose1976algorithmic`, `tarjan1984mcs`, `corneil2008unified`, `berry2004mcs`, `brandstadt1997lexbfs`, `ibarra2008dynamic`, `banerjee2018maintaining`, `mezzini2012fully`, `gueneau2019formal`, `even1981maintaining`, `baswana2016dynamic`, `ramalingam1996dynamic`, `lammich2015dfs`, `lammich2014gabow`, `morse2026bfs`.

Zero missing keys, zero duplicate keys, zero uncited keys.

## 9. Citation occurrence-level ledger

20 `\cite` occurrences across the 15 works; each attribution checked against the source's hypotheses and scope. No retractions/corrections outstanding. The Corneil–Krueger incomparability claim and the brute-force witness (204/204, symmetric difference 40) are reproduced in the artifact README.

## 10. External-artifact manifest (live verification, 2026-10-21)

| Field | Value |
|---|---|
| Repository | https://github.com/thonmay/mcs-lean (renamed from `thesis-lean`; the old URL answers 301 to the new one) |
| Public (unauth) | HTTP 200 |
| Pin | signed annotated tag `mcs-arxiv-v10` (Lean proof + docs + `scripts/stab.c`, `scripts/probe_check.py`, `scripts/prefix_hypothesis_count.py`); GitHub Release `mcs-arxiv-v10` (Latest; v9 and v7 retitled superseded; the template's `v4.35.0-rc2` release retitled "Toolchain bump ... (not a paper artifact)" and marked pre-release); Software Heritage revision `swh:1:rev:0d0ddffbcef5817c50a073a350428edd2da5bfb5` (API HTTP 200 after a save request) |
| Tag dereference (unauth `git ls-remote`) | `mcs-arxiv-v10^{}` → `0d0ddffbcef5817c50a073a350428edd2da5bfb5`; differs from `ab521f2` only in `AxiomAudit.lean`, `scripts/check_axioms.sh`, `README.md` (CI green; aiserver lake build, defs-sync, axiom audit 41+6, leanchecker 20 modules) |
| Palomar | v3 submission `um08gqgsunmk` from `ab521f2`: review `704cc036`, no blocking problems, no warnings; registration consented 2026-10-19T13:10Z; status `registration-paused` (operator attention) as of 2026-10-21, public v3 JSON 404. The paper cites v2 and states that v2 holds the every-vertex form of the two prefix theorems. Earlier v3 attempts withdrawn: `7hz177t19zlj` (blocking: unproved 2P3 minimality wording), `4xtu7q8i9py2` (warning: README universal P3 claim); both fixed. |
| Commit files reachable at pin | `README.md`, `comparator.json`, `AxiomAudit.lean`, `scripts/check_axioms.sh`, `scripts/probe_check.py`, `scripts/prefix_hypothesis_count.py`: all 200 |
| Role | Logically required (all theorems) |
| Visible in paper | Yes (reproducibility paragraph, `sec:formalization`) |
| In Comments | Yes |
| License | Apache-2.0 (repo) vs CC BY 4.0 (arXiv manuscript) — separate, intentional |

## 11. Final ZIP allowlist, manifest, and two-path build

- Allowlist (one path per line): `main.tex`, `references.bib`, `main.bbl`.
- ZIP members (verified, `allowlist_matches: true`): `main.tex` (58021 B), `references.bib` (8278 B), `main.bbl` (5557 B). No build debris, no PDF, no code, no Lean sources, no audits.
- Full-source build (aiserver, TeX Live 2021): LaTeX → BibTeX → LaTeX ×2, exit 0, 15 pages, 0 overfull, 1 underfull.
- Shipping build (extracted ZIP, no BibTeX/Biber): all rc=0, 15 pages, 48033 selectable-text chars, 32/32 fonts embedded, 0 undefined citations in the final run, 0 overfull, 1 underfull.
- `.bbl` byte-identical: `matches_shipped_bbl: true`.
- ZIP SHA-256: `91d39f7f89dda3484d5e5e02862f96861f6d7fb97d8a772fc0fee157521c9982`.
- `archive-built.pdf` SHA-256: `7ff5b13d4d16592e5e6577c3c484e3e7e968e23f1f01d07677c143ba58d01c63`.

## 12. Rendered-PDF audit

15 pages, letter, selectable text, fonts embedded (`pdffonts` 32/32 `emb yes`). Title, authors, affiliations, abstract, acknowledgements/CI, artifact URL, references all render. No line numbers, highlights, watermarks, or referee material. One underfull hbox (source lines 575–579, the Theorem 14 header with its long Lean-name list, badness 3428): **cosmetic**.

## 13. Authorship, affiliation, AI disclosure, rights

- Authors: Md Thoriqul Islam Thonmay (first; ORCID 0009-0009-8317-6645, public record name matches, checksum valid), Gregory Morse (no ORCID given). Both ELTE, Department of Programming Languages and Compilers. Author order unchanged. Submitter is the first author.
- AI disclosure: visible unnumbered section; provider + exact model ID + thinking mode + role for all four models, plus who produced the internal review rounds, `stab.c` and the $2P_3$ witness (second author, Claude Opus 5.5) and the probe and prefix-hypothesis scripts (first author, same model); "No AI system is an author"; authors accept full responsibility. Divergence check (metadata line vs visible text) passes: the metadata field copies the visible paragraph verbatim.
- Rights: arXiv license CC BY 4.0 (author-confirmed); repository Apache-2.0; third-party deps (Lean 4, Mathlib) under their own licenses.

## 14. Checksums

`main-upload.zip` SHA-256 above; `clean-build.bbl` and the in-ZIP `main.bbl` byte-identical (5557 B). Recompute after any further change.

## 15. Exact edits made this session

1. Added the `\iffalse` metadata region before `\begin{document}`.
2. Replaced the Acknowledgements/AI section with provider + exact model ID + role wording (removed vendor-generic phrasing).
3. Added a visible `Artifact and reproducibility` paragraph with the public repo URL, tag, commit, and role distinction.
4. (Earlier) Comparator count 36 → 37; online corollary promoted from observation to `Corollary` (`common_order_extends_prefix`); contributions bullet updated.
5. Created and pushed annotated tags `mcs-arxiv-v1` (on `a872fdd`, session 1) and `mcs-arxiv-v2` (on `a92df35`, adds the public verification scripts).
6. (Supervisor-feedback pass, 2026-10-13) Section 7: stated that the no-break insertion bound $|\mathrm{pos}(u)-\mathrm{pos}(v)|$ includes the later endpoint's position, which the executable probe checks but Lemma `no_break_at_laterPos` shows never fires, so the proved bound is one unit above the open-window optimum. Cost-model paragraph (Sec. 1) and Sec. 7: a cost unit is "superconstant, up to $\Theta(n^3)$" rather than "$\Theta(n^3)$". Artifact unchanged (still `mcs-arxiv-v3` = `53ce492`).
7. (Palomar review `f4c1ed17`, 2026-10-14) `common_order_extends_prefix` re-proved under the prefix-only bounds of `exists_common_ordering_prefix` (previously every-subset bounds). Corollary 1 and the contributions bullet now say "under the same hypothesis". Artifact re-pinned to `mcs-arxiv-v4` = `c4c2c0f` (lake build, defs-sync, axiom audit, leanchecker on all 20 modules, CI green).
8. (Draft review, 2026-10-14) New title ("How rigid is maximum cardinality search? ...") and a stability-first abstract (1456 chars); the unhedged "first locality analysis / first machine-checked" sentence is dropped. Palomar paragraph rewritten: the audit-surface phrase is a v1 *trust reason*, not a review warning; v1 is from ancestor `a872fdd` (37 of 41 names, every-subset online corollary); v2 of `c4c2c0f` submitted, registration pending. Intro and conclusion no longer claim every theorem is in Lean (the sublinear probe bound is a paper proof). Theorem 1 says "proper" prefix; Theorem 7 also cites `legal_upto_earlierPos`; `exists_common_ordering` now cited in Sec. 3 (makes the "9 in Section 3" count and the table row correct); deletion described as a parallel procedure, not a specialization; unsourced "~90% / ~96%" win-regime figures removed. Page count 12 → 13.

9. (Palomar v2 registered, 2026-10-15T01:03:25Z) Sec. 7 and the reproducibility paragraph now cite version 2 (pinned commit `c4c2c0f`, outcome `neutral`, no review warnings, trust `high`, 742 Challenge lines) as the registered record, superseding v1 from ancestor `a872fdd`; footnote URLs point to `version=2` / `-v2.json` (both HTTP 200).

10. (Style pass, 2026-10-15) Prose of the introduction, contributions, cost-model paragraph, formalization and artifact paragraphs, related work and conclusion reworded by hand, using rewrites proposed by the self-hosted Humanizer 12B model as suggestions; theorem statements, proofs, Lean names, numbers and the abstract were not passed through it. The model is now named in the AI disclosure (visible text and metadata, identical). The artifact paragraph now also excepts the paper-level probe bound from "every positive statement is a theorem".

11. (Supervisor round-2 checks, 2026-10-19) Lean: `exists_common_ordering_prefix` and `common_order_extends_prefix` now require the count bounds only for vertices not in the common prefix (strictly more general; `exists_common_pick` takes the same restricted bounds); the `exists_common_ordering` docstring says "every subset", which is equivalent to adding a matching. `formalization.yaml` gains its four missing comparator entries (41/41). Repository renamed to `mcs-lean`, library `ThesisLean` → `McsLean`; all 22 Lean files are otherwise identical to `c4c2c0f` except `Challenge.lean`, `Solution.lean`, `McsLean/Stability.lean`. Artifact re-pinned to `mcs-arxiv-v7` = `5cd2ca7` (lake build 8975 jobs, defs-sync, axiom audit, leanchecker on all 20 modules, CI green). Paper: Theorem 1, the online corollary, the abstract and contributions state the unchosen-vertex hypothesis; the matching equivalence of the every-subset form is proved in two lines; exhaustive counts (non-matching updates covered: 48/100 at n=4, 1020/5315 at n=5; no unsound case) and the n=3 P3 example are added. The sufficient-not-necessary example is now explicit (n=4, prefix (3,1,2)). Probe theorem: the claim "the delete probe is an O(1) check" is withdrawn (the hosts {01,02} and {01,12} share order and (M_j) but differ on deleting 01); the deletion break test needs runner-up data and maintaining it is stated as open. The proof now locates the *first* break (successor query plus augmented-tree descent), and the no-break update cost is O(log n). Random-graph checks against recomputation are quoted and reproduced by the new artifact scripts. "The hypotheses are sharp" replaced by "neither part of the hypothesis can simply be dropped". Palomar paragraph states that v2 is registered from the ancestor `c4c2c0f` and which two statements changed since.

12. (2026-10-19, after the subagent audit of every referee item) Theorem 4 now attributes initialization to `init_valid` and the full-prefix identity to `greedySuffix_full`; the comparator paragraph explains why the table groups by *stated* section while the sentence counts *first named* section; introduction states the contribution as the first locality analysis and first machine-checked incremental repair of MCS orderings (hedged, survey cited); author emails in title footnotes, first author marked BSc student; AI disclosure gives a thinking mode per model and discloses that the internal review rounds and their check scripts (`scripts/stab.c`, probe and prefix-hypothesis scripts) came from AI agents run by the second author; "the referee's C checker" reworded; GitHub Release and Software Heritage archive mentioned. A subagent claim that the incomparability witness is not chordal was checked and rejected (its cycle used two non-edges; simplicial elimination succeeds). Page count 13 -> 14.

13. (2026-10-19, Palomar v3 reviews) Obstruction minimality is now presented as a computer-search result, not a theorem (Theorem 3 note, introduction, artifact docstrings); the non-monotone break example is n=4 (the n=5 one was called minimal and was not); the README separates Lean theorems from paper-level and tested statements. Artifact re-pinned to `mcs-arxiv-v9` = `ab521f2` (Lean statements identical to v7; docstrings only). Software Heritage SWHID added.

14. (2026-10-19, rendered-PDF review) All 14 pages rendered at 110 dpi and reviewed visually page by page, then re-reviewed after the fix. Found and fixed: a stranded first line at the bottom of the Related-work page and a single "2." line at the bottom of the obstructions page (now `\clubpenalty=\widowpenalty=10000` and two `$F$-degree~$2$` ties). Measured with `pdftotext -bbox`: no text line ends more than 2.1 pt past the 540 pt text edge (normal TeX tolerance; 0 lines beyond 543 pt); the Lean listing stays inside (max 537.4 pt). All 6 external links resolve (GitHub repo, two Palomar v2 URLs, arXiv 2604.12370) or are mailto; 89 internal links; 32/32 fonts embedded; `⟨ ⟩` and other Unicode glyphs in the listing render. Accepted as cosmetic: mid-name wraps of long monospace Lean identifiers in theorem headers, and the Theorem 14 header's loose line (the one underfull box).

15. (2026-10-21, supervisor round 3) B1: Theorem 14 now states `exec_insert_update_eq`/`exec_delete_update_eq` exactly (both matrices symmetric and loop-free, `FlipOf`, canonical ordering of the *old* graph, deletion edge hypotheses; display equation). B2: bibliography corrected against Crossref/doi.org (Donald J. Rose, R. Endre Tarjan, George S. Lueker; Baswana et al. key `baswana2019dynamic`, DOI 10.1137/17M114306X; `{G}abow's ... Component`; Shiloach-Even author order; dynamic topological order now cites Pearce-Kelly JEA 2007 and Bender-Fineman-Gilbert-Tarjan TALG 2016 instead of Ramalingam-Reps; Morse-Kozsik described as BFS only, LexBFS left open, checked against the arXiv v1 text; stale "re-verified against Crossref" header replaced). B3: abstract and Sec. 8 say the external kernel re-check is at the pinned commit and that Palomar v2 holds the every-vertex form; v3 pending. 4.2/4.3: paragraph after Theorem 2 (lower bound at singleton prefixes forces E(G) in E(G'); hypothesis is not a practical test). 4.4: "combinatorial core/heart" replaced; AxiomAudit gains an AUX block for the six cited lemmas (artifact re-pinned to `mcs-arxiv-v10` = `0d0ddff`, statements byte-identical to v9). 4.5: Lemma 11 "justifies shrinking", executable still checks pos(v). 4.6: deletion proof covers S after pos(v), cites `legal_after_laterPos`. 4.7: abstract cost sentence dropped. Minor 1-6: review-response phrasing removed, "iff" -> "roughly when", cost item 4 "within one unit", probe preprocessing O(n log n)/O(n), appendix helper names pointed to `Challenge.lean`, SWHID is now a revision ID. ORCIDs not added. Subagent review of the diff: all items addressed and correct; three prose fixes applied. Visual review of all 15 pages: clean. Page count 14 -> 15.

16. (2026-10-31, supervisor round 4: "ready for arXiv") Optional items: Sec. 8 now says v3 "has been submitted and is awaiting registration" (the registry review cannot be checked by readers until v3 is public); related work says "the Even--Shiloach tree" so the citation's Shiloach-Even author order reads as intentional. Morse ORCID not added (author's choice). Repository: merged `v4-work` branch deleted; `v4.35.0-rc2` tag kept, its release already retitled as not a paper artifact. Pre-flight: `main.bbl` is in the ZIP; the bundle has no `MCS-arxiv-draft/` directory (allowlist is main.tex, references.bib, main.bbl); CI on `0d0ddff` is green. Posting deferred by the author until Palomar v3 registers.

## 16. Official policy sources

Bundled snapshot `references/arxiv-policy.md` (baseline 2026-08-30). Live pages to re-open at submission: https://info.arxiv.org/help/submit_tex.html, https://info.arxiv.org/help/prep.html, https://arxiv.org/category_taxonomy, https://info.arxiv.org/help/license/index.html. Access date for this audit: 2026-10-04.
