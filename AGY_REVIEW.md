# Review of fix/antigravity-support (2026-11-27)

Decision: only the skill install and doc lines are taken into main. The
`provider: agy` backend stays on this branch: it is new engine code four days
before submission, it has not run against a real `agy` binary, and the thesis
describes the providers api, opencode and mock only. Do not open it again
before the thesis is submitted.

Taken into main (rewritten):
- `skill_targets("user")` adds `~/.gemini/config/skills`, the global folder
  that both the Antigravity App and the CLI read
  (https://antigravity.google/docs/skills). `~/.gemini/antigravity-cli/skills`
  is CLI-only, so it was not used.
- README, SKILL.md and the `--harness` help mention agy.
- Test: `test_skill_install_reaches_antigravity_user_dir` installs the skill.

To fix before the backend can be merged (verified against
https://antigravity.google/docs/cli/headless/ and /docs/cli/reference/):
1. `-p` takes the prompt as its value. `[bin, "-p", "--output-format", ...]`
   makes the string `--output-format` the prompt. Put the prompt directly
   after `-p`, and change the redaction in `HarnessBackend.run()`, which
   assumes the prompt is the last element.
2. The JSON key for the final text is `response`. `result` is only the
   stream-json event wrapper. The usage keys are `input_tokens` and
   `output_tokens`.
3. Env: drop `GEMINI_API_KEY`, `GOOGLE_API_KEY` and the `GEMINI_` prefix.
   Headless mode uses the cached login in `~/.gemini/antigravity-cli/` and
   ignores `GOOGLE_API_KEY`. `GEMINI_API_KEY` works only with
   `"modelProvider": "gemini"` in settings.json. Keys in the env are readable
   by the agent and land in recorded tool output. Allow-list exact names
   (`AGY_PATH`, `AGY_ADC_AUTH`) only.
4. Tests: run `AgyBackend.run()` through the jail with a fake `agy` (like
   `FAKE_OPENCODE` and the plant test in tests/test_agents.py), not only argv
   and parse.
5. Keep the "verified for Claude Code 2.1.303 / Codex 0.163.0" note in the
   `skill_targets` docstring.
6. The comments at harness.py:7-8 and config.py:89,106 still say
   opencode-only. The UI (server.py:122, :147) cannot pick agy; either add it
   there or say so.
7. Once it works, the thesis provider lists (Ch2, Ch3 FR-AGENT, Ch4) need the
   new provider too.
