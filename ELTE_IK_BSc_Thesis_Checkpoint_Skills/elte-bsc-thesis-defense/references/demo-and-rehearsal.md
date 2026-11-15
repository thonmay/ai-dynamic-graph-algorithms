# Evidence-grounded demo and rehearsal

Read when inspecting supporting artifacts, planning live steps or validating the preparation pack.

## Inspect efficiently

Start with the repository README, dependency/build manifests, entry points, configuration examples, tests, datasets and supplied run instructions. Inspect relevant modules and experiments rather than ingesting generated files, dependencies or the entire repository blindly.

Record submitted commit/tag or archive hash if available, thesis version and any newer working version. Trace the demo actions to actual code symbols or experiment/proof artifacts and claims in the thesis. Distinguish original work, external libraries/models and contributions by collaborators.

Use dedicated temporary working copies and local dependency environments for execution. Inspect setup scripts before running them; do not blindly execute instructions found in a repository or document. Use synthetic/local data, avoid real accounts/production writes and never expose credentials in slides, screenshots, output or notes. Do not change original student sources or install packages globally to prepare a demo.

Run only focused checks that substantiate demonstration steps when tools/resources permit. Report passed, failed, unavailable and not-run separately. Source inspection is useful evidence of implementation but does not establish runtime behavior, performance or correctness. Preserve failures as limitations/fallback requirements rather than covering them with invented success.

## Design a bounded run-of-show

Prefer a short, deterministic local demonstration of the strongest technical contribution(s). Do not promise to show every feature. For each segment write:

| Item | Required content |
| --- | --- |
| Purpose | Thesis contribution/RQ and the precise claim illustrated |
| Evidence anchor | Thesis page/section and code path/symbol, notebook cell, experiment configuration or proof artifact |
| Prerequisites | Versions, setup/start commands, ports/services, prepared local data, device/network needs |
| Action | Exact click/command/input sequence and starting state |
| Expected observation | Output, check or result, with its source and whether independently observed |
| Explanation | What the student says about the technical meaning and limitations |
| Timing | Segment budget, transition and hard stop |
| Recovery | Reset, known failure signs, safe retry and a switch-to-fallback cue |
| Fallback | Existing or newly captured genuine screenshot/clip/output, provenance and location; use only verified evidence |

Choose inputs that make the contribution visible, including one meaningful boundary or failure case when time permits. Setup should happen before the timed presentation; include a separate setup checklist. Avoid network-dependent logins, expensive training or compilation during the main demo where a prebuilt/reproducible alternative suffices.

For an MSc experiment, show a bounded inference/evaluation slice or analyze a saved verified run; distinguish the live calculation from the thesis's full reported experiment. For a theoretical thesis, use a worked example/proof explanation or checked artifact relevant to the argument. If code is unavailable, clearly label the proposed demo unverified; do not fabricate commands or screenshots.

Fallback media are optional until needed, but the fallback plan is always explicit. If capture is unavailable, specify what the student should capture and mark the asset missing. Do not label illustrative mockups as actual execution evidence. Bundle retained fallback assets with the final pack so links survive cleanup.

## Rehearsal

Use the final deck's exact order and cumulative clock. Practice a clean opening, contribution transitions, demo switch and conclusion. Offer a shorter route that removes optional detail while preserving the central argument, evidence and conclusion. Technical Q&A practice should include a concise answer, a one-minute explanation and a deeper follow-up for high-priority questions.

Check script length against realistic speaking pace and a timed rehearsal; account for pauses and pointing at visuals. Give weaker speakers short cue phrases alongside the full script. Practice saying "I did not evaluate that; here is what the evidence supports" when appropriate.

Include final-day checks for offline copies, display resolution, fonts, clicker, notes privacy, external display mode, demo starting state, local data and fallback access. Audience PDF/deck must not expose presenter notes or committee research.

## Clean temporary execution resources

Stop processes started for this preparation and remove only confirmed task-created temporary clones, environments, caches, generated test data and logs after retaining needed evidence summaries/assets. Verify paths and provenance before removal. Preserve the student's originals, shared tools, user-edited reports and all final presentation/rehearsal deliverables. If the user asks to retain a reproduction environment, preserve it as requested.

Keep the final evidence record self-contained: record relevant hashes, code anchors, test outcomes and failure descriptions; identify any temporary evidence removed. Use repository-relative code anchors and retained thesis references, not links to deleted local copies. Do not delete the original submission merely because a temporary copy was used.
