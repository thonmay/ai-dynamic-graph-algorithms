# Lean Skills + MCP Setup (opencode)

Two Lean MCP servers, two skill packs. They complement each other:
**lean-lsp** for exploration/mathlib search (and as backend for lean4-skills),
**lean-beam** for fast speculative proof iteration without lake rebuilds.

## Upstream repos

| Project | GitHub |
|---|---|
| lean-lsp-mcp | https://github.com/oOo0oOo/lean-lsp-mcp |
| lean-beam (leanprover-skills) | https://github.com/leanprover/lean-beam |
| lean4-skills | https://github.com/cameronfreer/lean4-skills |

The copies under `skills/lean/` are vendored snapshots; update by re-cloning upstream.

## Prerequisites

1. **elan** (Lean toolchain manager): `curl https://elan.lean-lang.org/elan-init.sh -sSf | sh`
   - provides `lean` and `lake`; projects pin a version via `lean-toolchain` file
2. **uv** (Python, for lean-lsp-mcp): `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **ripgrep** (recommended): `brew install ripgrep` — used by local search + lean_verify
4. A Lean/Lake project: `lakefile.toml` + `lean-toolchain` in project root
5. Run `lake build` once manually — first MCP start reuses the built environment
   (avoids client timeouts during the initial `lake serve`/elaboration)

## Skills

Skill packs live in this repo (`skills/lean/`) and are copied into opencode's skill dir:

```bash
rsync -a --delete skills/lean/lean4/     ~/.opencode/skills/lean4-skills/
rsync -a --delete skills/lean/lean-beam/ ~/.opencode/skills/leanprover-skills/
```

`opencode.json` must list `"skills": { "paths": [".opencode/skills", "~/.opencode/skills"] }`
(already configured here).

- **lean4-skills** — workflow plugin: `/lean4:prove`, `/lean4:golf`, `/lean4:disprove`, ...
  It drives the **lean-lsp MCP** tools (hard-wired to them: `lean_goal`,
  `lean_multi_attempt`, `lean_leanfinder`, `lean_loogle`, ...). No lean-lsp = plugin can't work.
- **leanprover-skills** (= lean-beam repo) — official leanprover agent tooling.
  Its SKILL.md documents the lean-beam contract: 0-indexed coordinates,
  `update` before probes, version-bound calls, speculative `run-at` + handles,
  `save` as single-module checkpoint (not batch build evidence).

Note: `~/.opencode/skills/lean4/` and `lean-beam/` are already-populated copies from the
respective installers; the `-skills` dirs above mirror this repo. Keep them in sync after
pulling updates.

## MCP servers

### lean-lsp

Runs via `uvx`, spawns `lake serve` in the project root:

```jsonc
"lean-lsp": {
  "type": "local",
  "command": ["/Users/thonmay/.local/bin/lean-lsp-wrapper",
              "--lean-project-path", "/path/to/lean-project"],
  "enabled": true
}
```

(Wrapper is optional; `["uvx", "lean-lsp-mcp", "--lean-project-path", ...]` works too.
Nix alternative: `nix run github:oOo0oOo/lean-lsp-mcp`.)

### lean-beam

Install once (puts `lean-beam`, `lean-beam-mcp`, `lean-beam-search` in `~/.local/bin`,
runtime under `~/.local/share/beam`):

```bash
cd ~/.opencode/skills/leanprover-skills   # repo checkout
./scripts/install-beam.sh --opencode      # or --claude / --codex / --all-skills
```

Then register:

```jsonc
"lean-beam": {
  "type": "local",
  "command": ["/Users/thonmay/.local/bin/lean-beam-mcp"],
  "enabled": true
}
```

The MCP owns its own session — do NOT also run `lean-beam serve` for MCP tool calls.
Requires `elan` on PATH. After reinstall, restart opencode so the MCP launches the
current runtime (check via `beam_version`: `runtime_current` must be `true`).

## After config changes

Restart opencode. Verify with a trivial call on each server
(`lean_goal` / `beam_version`) before real work.

## Gotchas

- **Coordinates**: lean-lsp is 1-indexed; lean-beam is 0-indexed for line AND character
  (empty lines accept only char 0). Silent `null` results usually mean off-by-one here.
- **lean-beam versioning**: every version-bound call needs the version from the last
  `update`/`sync`; after any real file edit, save + `update` before the next probe.
  On `contentModified`, retry with `error.data.acceptedVersion` — don't guess.
- **lean-beam save** checkpoints one module in the *server* environment; it does not
  validate downstream importers. Final proof of correctness = clean `lake build` / CI.
- **lean-lsp first call** can be slow on big files (full elaboration); poll, don't panic.
- **Which to use**: mathlib search / `/lean4:*` workflows → lean-lsp;
  grinding out a proof with speculative probes → lean-beam.
