# ELTE IK BSc thesis consultation checkpoints — universal build

The five consultation-course checkpoint skills for the BSc thesis, packaged so each
folder loads as an Anthropic Agent Skill and as an OpenAI skill. Separate from the
official 30-point thesis review, which lives in its own bundle.

| Skill | Scope |
|---|---|
| `elte-bsc-audit-topic-plan` | Checkpoint 1 — topic registration, proposal, work plan |
| `elte-bsc-audit-requirements` | Checkpoint 2 — requirements and planning package |
| `elte-bsc-audit-architecture` | Checkpoint 3 — architecture, business rules, class diagram |
| `elte-bsc-audit-implementation` | Checkpoint 4 — runnable 60–70% implementation |
| `elte-bsc-audit-final-thesis` | Checkpoint 5 — completed thesis, submission readiness |

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

This bundle contains one zip per skill, which is the unit every installer expects. No loose folders:
a skill zip must have the skill directory at its root, so the zip is the shippable object.

**Claude.ai / Claude Desktop** — Settings → Capabilities → Skills → upload. Upload each `.zip` in this folder, one at a time — 5 uploads.

**ChatGPT** — upload the same per-skill zips; `agents/openai.yaml` still applies there.

**Claude Code / Codex** — these read skills as directories, not archives, so unzip
straight into the skills directory:

```bash
for z in *.zip; do unzip -q "$z" -d ~/.claude/skills/; done   # personal, all projects
for z in *.zip; do unzip -q "$z" -d .claude/skills/; done     # or project-scoped
```

**Claude API** — unzip, then upload the folders via the Skills endpoint and reference the
skill ID in your request's container config.

## Before trusting these on a real submission

Neither of the following has been tested — they're the two things worth checking first.

**Environment assumptions.** Several bodies say to refresh the official deadline PDF and the supervisor
guidance when internet access is available, and to render PDF or Word files when layout
affects the result. Both depend on which tools the surface exposes — the freshness check
in particular is what your authority rules lean on, and it silently degrades to the
bundled snapshot when the surface has no web access.

**Triggering.** Anthropic surfaces `name` + `description` and lets the model decide
whether to open a skill; Claude tends to skip skills for work it thinks it can do
unaided. A terse "check my thesis" may not pull one in, while "audit this against the
BSc checkpoint 3 architecture criteria" reliably will. Five siblings describing adjacent stages of one process is a hard case for
skill selection; the negative clauses in each description ("Do not use for other
checkpoints") are what keep them apart. If under-triggering shows up, fix the
`description`, not the body.
