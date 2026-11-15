---
name: elte-bsc-thesis-defense
description: Prepare an ELTE BSc thesis defense with PowerPoint or Beamer slides, speaker notes, a code-based demo and committee-tailored Markdown practice questions. Use with a thesis and supporting code.
---

# ELTE BSc thesis defense preparation

Create a polished, evidence-grounded presentation and complete preparation pack for the thesis portion of an ELTE BSc defense. Keep the technical contributions central and help the student explain their own work confidently.

## Read first, then ask once

Inspect supplied thesis files, repository, reviewer feedback and prior chat before asking anything. Prefer the submitted PDF together with editable Word/LaTeX source and associated figures/bibliography; source-only or PDF-only is usable. Extract the student's name, Neptun code if present, exact title, supervisor, programme, language and own-work statement. Do not ask the student to repeat those facts. Include Neptun code only where required or requested; it is not necessary on every slide.

Build an input inventory with accessible locations, versions and unresolved discrepancies. Use the submitted thesis as the record of defended claims; use source and code to substantiate them. A newer working branch is not evidence that an improvement was in the submitted work. Ask only when a version conflict changes the defense.

If material information is missing, send one combined request, adapted to omit everything already known:

> Please provide the remaining items together:
> - An accessible thesis PDF and, ideally, its Word/LaTeX source with figures and bibliography; either source or PDF is enough to start.
> - A repository link, archive or local code path, preferably the submitted commit/tag, plus setup instructions and any existing demo assets. For theoretical work, provide the proof, notebook or other supporting artifact instead.
> - Your actual defense committee: paste member names/roles from the assignment email or Neptun notice, and its relevant instructions. Include institutional emails/profile links if available to disambiguate names; redact unrelated personal details. A committee number alone needs programme/language/sitting context.
> - Any committee research/profile audit you or your supervisor already have, or a link to it. If absent, I will research the assigned members using the supervisor's guide and official profiles.
> - The confirmed presentation/demo time limit and whether Q&A is included, defense date if known, language, selected final-exam topics/subjects, reviewer questions and any equipment/network restrictions that are not already in the files.
> - Your preferred slide format: editable PowerPoint (.pptx), LaTeX Beamer, or both; and an existing required template if there is one.

Do not require both thesis formats, a public repository, every committee member's email, a prepared committee audit, or a complete final thesis audit. For private material, use accessible authorized uploads/local paths rather than requesting publication or credentials. A pasted assignment email means committee information, not permission to contact anyone.

If only a cosmetic preference is missing, proceed with stated defaults: match the thesis language, use a clean 16:9 design and offer PowerPoint / Beamer / both with editable PowerPoint as the default. If committee or code is unavailable, continue with the grounded core pack and label the corresponding tailoring/demo as provisional; do not claim a complete committee-specific or verified live-demo result. If there is no usable thesis content, request it and do not invent a completed thesis. Follow up only for newly discovered consequential gaps.

## Ground the defense in evidence

Read [references/elte-sources.md](references/elte-sources.md) for source priority and current ELTE checks. Verify applicable programme/curriculum and sitting rules before using a default duration; do not confuse the thesis presentation with the entire final examination.

Read [references/committee-research.md](references/committee-research.md) when tailoring to assigned members, and [references/demo-and-rehearsal.md](references/demo-and-rehearsal.md) when inspecting code, planning the demonstration and rehearsing. These references are bundled here; no other skill is required.

Prepare a compact claim-evidence map: contribution or research question, student ownership, thesis section/page/figure, code path/symbol or experiment/proof artifact, evidence status, slide/demo use and limitations. Distinguish thesis-reported results, repository evidence, independently reproduced results and unverified claims. Static inspection is not a passed runtime test. Never invent features, measurements, citations, screenshots, study participants or successful execution.

Resolve missing support through honest wording, an explicit limitation or a question when essential. Do not silently fix research results or add an uncompleted contribution. Use relevant reviewer questions and supplied audit findings to prepare candid answers, not to alter assessment conclusions.

## Build a BSc technical story

Use the thesis's three principal contributions as the narrative spine: problem -> solution -> validation. For each, show the useful design decision, implementation evidence, acceptance/testing result and trade-off. Group related features into three coherent contributions without inventing work; if the evidence supports fewer, say so rather than manufacture a third.

Explain architecture and an end-to-end path through the system. Show why the student's choices were appropriate, what they implemented themselves, how failure cases are handled, and what tests actually demonstrate. Keep motivation, user-documentation details and conclusion brief.

Integrate the student's registered exam topics/subtopics naturally through concrete thesis evidence. Avoid slides labelled "Exam Topic 1/2/3" or a generic syllabus lecture. Missing registered topics need not stop the thesis presentation; mark subject mapping provisional and never replace the student's registration with a recommendation.

Unless applicable official instructions say otherwise, use the supervisor's 12-minute rehearsal target: about eight minutes of slides and four of live demo within the original 10-15 minute guidance. This is guidance, not a universal ELTE regulation. The official BSc page contains an old-regulation 15-minute clause; do not apply it to a different curriculum without checking the applicable linked rules.

Include introduction, system overview, contribution sections, a visible demo transition, and conclusion with genuine limitations/future work. Keep the contribution balance sensible without forcing identical structures. Include a dedicated demo block when feasible and budget transition time within it.

## Produce the full preparation pack

Use [references/presentation-formats.md](references/presentation-formats.md) for the chosen PowerPoint/Beamer output, notes and visual verification. Make the actual editable deck/source, not merely an outline, when the environment can create it. Produce both formats when requested from one synchronized storyboard.

Deliver the following, with filenames adapted only when the user has an established convention:

1. **timing-plan.md** — slide/segment title, purpose, duration, cumulative start/end timestamps; demo start/end and transition; target total and source/default status; shorter route and Q&A treatment. Count demo time once.
2. **defense.pptx and/or defense.tex** — the chosen editable presentation with required local assets/build instructions, plus a clean audience PDF when export/compilation is available. Clearly distinguish backup slides from timed main slides.
3. **speaker-notes.md** — for every main and backup slide, a point-plan checklist and natural spoken script, timing/transition cues, plus rehearsal questions and concise defense hints on technical slides. Embed the same notes in the presentation format. Write support for confident delivery without requiring the student to read a dense essay.
4. **demo-plan.md** — code-grounded run-of-show with exact steps, inputs, expected outcomes, technical meaning, timing, prerequisites, reset and recovery, and fallback evidence. Include its shortened cues in slide notes.
5. **committee-brief.md** — assignment provenance, matched identities, verified public expertise and thesis connections, sources/dates and explicit limits. If unassigned, provide a provisional subject-based brief without guessing a panel.
6. **defense-questions.md** — a Markdown rehearsal bank, organized and prioritized for this thesis. Include question, why it matters, relevant contribution/RQ, concise answer checkpoints, a thesis/code/result anchor, an honest limitation and a probing follow-up where useful. Label committee-specific connections as practice inferences. Cover all main contributions, decisions, tests/evaluation, limitations, own work and supplied reviewer questions; tune depth to BSc or MSc. Prioritize roughly 15-25 useful questions rather than padding to a quota.
7. **rehearsal-checklist.md** — a practical timed rehearsal plan, technology checks, opening/closing and demo transitions, likely time cuts, unknown-answer handling and a short final-day checklist. Include short/standard/deep answer practice and advice for a technical failure.
8. **evidence-and-sources.md** — compact claim-evidence map, source dates/scope, thesis/code versions, reproduced checks and failures, unresolved discrepancies and assumptions. Keep this supporting record out of audience slides.

When file creation is unavailable, provide clearly labelled file contents and a complete slide-by-slide specification/source with all notes, demo and questions; state which requested binary outputs could not be created. Do not call an outline a finished .pptx or claim an uncompiled source is a verified PDF.

## Validate and hand over

Check factual grounding, ownership, source correctness, consistent slide numbering/notes, timing arithmetic, note/script speaking time, and all demo transitions. Visually inspect rendered slides and exported notes where tools permit, fix clipping/unreadable figures and verify selected output formats. Validate demo steps in a local isolated environment when possible; report what ran and what remains untested. Keep Q&A prompts/answers and personal committee research out of the clean audience deck.

Link the finished files with a concise readiness summary and material unresolved items. Rehearsal suggestions and committee tailoring must support sound explanations of the actual work. Do not claim to predict exam questions, guarantee success, send messages, publish the material or submit it to ELTE.
