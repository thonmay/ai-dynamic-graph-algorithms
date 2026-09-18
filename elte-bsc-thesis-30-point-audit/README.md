# ELTE IK BSc thesis 30-point audit — universal build

The official seven-criterion, thirty-point BSc thesis review, packaged so the folder
loads as an Anthropic Agent Skill and as an OpenAI skill. Separate from the consultation
course checkpoints, which live in their own bundle.

| Skill | Scope |
|---|---|
| `elte-bsc-thesis-30-point-audit` | Full 30-point audit — intake and parity, difficulty and propagation, exam-topic evidence, structure and appearance, user documentation, solution plan, implementation and code, testing, execution demo, report schema |

## What changed in the skills

Nothing. Every `SKILL.md`, `references/*.md`, `assets/icon.svg` in this bundle is
byte-identical to the original upload. The skills were already written in the layout
Anthropic uses — `SKILL.md` with `name`/`description` frontmatter, plus `references/`,
`scripts/`, `assets/` — so the port is repackaging, not rewriting.

Checked against what actually breaks an Anthropic load, all pass: names are valid slugs
matching their directories, descriptions are well under the 1024-char limit, frontmatter
carries no unsupported keys, every relative `references/…` link resolves, no reference
file is orphaned, and no body contains ChatGPT/Codex/Atlas wording or `$skill` invocation
syntax.

`agents/openai.yaml` is kept in each skill. It holds ChatGPT UI metadata (`display_name`,
`short_description`, `default_prompt`, icons, `policy.products`,
`allow_implicit_invocation`). Anthropic has no equivalent — presentation comes from
`name` + `description`, and implicit invocation is already the default — and Anthropic
loaders ignore unrecognised directories. So the file is inert on Anthropic and still live
on OpenAI, which is what lets one folder serve both. If a strict validator ever objects:

```bash
find . -maxdepth 2 -name agents -type d -exec rm -rf {} +
```

## Installing

This bundle contains a single skill zip, which is the unit every installer expects. No loose folders:
a skill zip must have the skill directory at its root, so the zip is the shippable object.

**Claude.ai / Claude Desktop** — Settings → Capabilities → Skills → upload. Upload the `.zip` in this folder.

**ChatGPT** — upload the same per-skill zip; `agents/openai.yaml` still applies there.

**Claude Code / Codex** — these read skills as directories, not archives, so unzip
straight into the skills directory:

```bash
for z in *.zip; do unzip -q "$z" -d ~/.claude/skills/; done   # personal, all projects
for z in *.zip; do unzip -q "$z" -d .claude/skills/; done     # or project-scoped
```

**Claude API** — unzip, then upload the folder via the Skills endpoint and reference the
skill ID in your request's container config.

## Before trusting these on a real submission

Neither of the following has been tested — they're the two things worth checking first.

**Environment assumptions.** The skill requires rendering and compiling the editable
source to establish source/PDF parity, and stops short of an exact final score when
parity can't be established. I previously flagged this as a hard blocker on sandboxes
without TeX — that was wrong. Claude's sandbox has `pdflatex`, `xelatex`, `latexmk` and
the poppler tools installed and working, so the parity and full-page-render requirements
are satisfiable there as well as in Claude Code. The remaining dependency is web access
for the official-deadline freshness check, which varies by surface.

**Triggering.** Anthropic surfaces `name` + `description` and lets the model decide
whether to open a skill; Claude tends to skip skills for work it thinks it can do
unaided. A terse "check my thesis" may not pull one in, while "audit this against the
BSc 30-point thesis review criteria" reliably will. It sits alongside the consultation-checkpoint skills, and its description
rules those out explicitly. If under-triggering shows up, fix the
`description`, not the body.
