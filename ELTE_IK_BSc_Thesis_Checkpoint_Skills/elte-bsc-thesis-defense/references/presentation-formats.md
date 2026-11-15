# Presentation formats and visual quality

Read for producing or checking the selected output. Use the environment's available presentation, PDF or document tools when they help; these skills must not depend on one vendor's tool names, another installed skill, a cloud service or a paid design API.

## Common storyboard

Establish stable slide IDs, titles, central claims, evidence anchors, visible content, visual, notes and timing before authoring. If both formats are requested, render the same storyboard into both; do not create divergent claims or missing notes. Create the complete chosen artifact rather than stopping after storyboard approval unless a material unresolved decision requires it.

Use a restrained academic design with generous space, consistent alignment/typography, strong contrast and readable projection sizes. Prefer architecture/flow diagrams, authentic system screenshots, selected result plots and compact comparison tables. Make the main takeaway visible on each technical slide. Keep code fragments short, explain axes/units and cite external figures/results where used. Use verified institutional assets/templates when supplied or available; do not invent an official ELTE logo.

Use actual thesis figures or redraw them faithfully with traceable values. Diagrams may be newly drawn to explain verified architecture, but new research findings and execution screenshots must never be fabricated. Avoid dense prose, ornamental stock visuals, overloaded tables and tiny references.

Every main and backup slide has two notes sections:

1. **Point plan:** concise speaking checklist, timing and transition/demo cues.
2. **Readable version:** full, natural spoken explanation consistent with the visible slide.

Technical slides also have brief **Practice questions / defense hints** with evidence-supported answers. These are presenter-only. Mirror all notes into speaker-notes.md by stable slide ID so they remain usable if a presenter application fails.

## PowerPoint

Create an editable .pptx with native editable text, shapes, diagrams and tables where practical; plotted figures/screenshots may be embedded images. Avoid flattening entire slides into images. Use a supplied required template when compatible.

Embed both notes sections and technical Q&A hints in the actual PowerPoint speaker-notes fields for every slide. Separate notes in Markdown are a fallback, not a claim that embedded notes exist. If the authoring tool lacks notes support, use a supported library/postprocessing route if available; otherwise disclose the limitation clearly.

Keep backup material identifiable and outside the timed main sequence. Verify the presentation opens, main slide count/order, notes, image embedding and absence of broken external asset links. Export a clean audience PDF where supported, render it and inspect every slide for overflow, poor contrast, cut-off labels, inaccurate formulas and unreadable charts. Inspect notes extraction or notes-page output too. State exactly which checks are unavailable if no renderer exists.

## LaTeX Beamer

Deliver defense.tex plus all required local assets, bibliography if used, engine/package requirements and a short build note. Source should compile with an available standard TeX engine; choose XeLaTeX/LuaLaTeX for required Unicode fonts or handle accents appropriately. Keep assets relative to the delivered source directory.

Copy [assets/presenter-notes.tex](../assets/presenter-notes.tex) into the output as presenter-notes.tex and input it once in the preamble. It retains the original prompt's three mode switches and exact two-argument presenternotes macro, adding mode validation and deferred option application. Call that macro for each frame, with item commands in the point plan argument and the spoken script in the second. Include technical Q&A hints as a labelled paragraph in the second argument or an additional note.

Select exactly one mode. The shared fragment defaults to notes-right; put these overrides AFTER inputting it and before beginning the document:

- Clean audience: PresenterNormaltrue, PresenterNotesOnlyfalse, PresenterNotesRightfalse.
- Notes only: PresenterNormalfalse, PresenterNotesOnlytrue, PresenterNotesRightfalse.
- Presenter two-screen PDF: PresenterNormalfalse, PresenterNotesOnlyfalse, PresenterNotesRighttrue.

Use proper LaTeX backslashes for these commands. Mode application is deferred to begin-document so these overrides take effect. Never leave multiple modes enabled. Generate separately named audience, notes and presenter PDFs when compilation is available; only the clean audience PDF is intended for projection/distribution. Keep the build mode explicit in any delivered source variants or build instructions.

Compile in a separate build directory, resolve errors and overfull elements, and inspect the rendered audience slides and notes. Verify formulas, Unicode names, citations and note completeness. A successful compile is not a visual check. If compilation is unavailable, still deliver complete source/assets/build steps and say that the PDFs and visual compilation check are unavailable.

The bundled fragment uses a compact notes heading instead of the default slide thumbnail to leave room for the full script. Check the longest notes explicitly: Beamer does not automatically paginate an overflowing note. Shorten repetition or use synchronized note overlays/continuations while preserving the complete script and its slide mapping. Multiple independent note pages after one frame may show only the last page in second-screen mode; do not assume they all appear. Never solve overflow by silently dropping the readable version or shrinking notes until unreadable.

## Timing validation

For each timed slide/segment record duration and cumulative start/end. Include demo transitions and any pause that belongs inside the permitted talk. Do not count the same demo as both slide time and separate demo time. Keep backup slides outside the target total. The sum must match the chosen target and any official limit; include Q&A only if that limit explicitly includes it.

Estimate speaking time from the actual notes and adjust content rather than compressing text into unreadable slides. Keep a documented shorter route for interruptions. If the requested duration conflicts with an applicable rule, honor the rule and explain the change.
