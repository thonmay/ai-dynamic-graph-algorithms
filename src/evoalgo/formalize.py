# AI-assisted code: generated and revised with DeepSeek-V4-Flash and Qwen3.8-Flash-Next
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Formalization runner: dispatch the lean-prover agent and verify its output.

Takes a run directory and a candidate that passed bounded verification, invokes
the lean-prover agent to produce an honest Lean proof of the candidate's
maintained invariant, then verifies the artifact:
  - `lake build` succeeds for the new module,
  - the module contains no `axiom` / `sorry` / `admit` / `unsafe` outside
    comments (text scan), and
  - `lean` reports no "declaration uses `sorry`" warning.

The outcome is written to <run_dir>/formalization/<candidate_id>.json so the
pipeline records whether the bounded empirical claim was upgraded to a
mathematical claim.

Usage:
  evoalgo formalize --run <run_dir> --candidate <candidate_id> [--model M]

The candidate must be at <run_dir>/candidates/<candidate_id>.py and must have
state PASS in the latest committed generation.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from .agents.harness import OpencodeBackend, harness_env
from .config import RunConfig

logger = logging.getLogger(__name__)

# The repository's own Lean project; LEAN_PROJECT points elsewhere.
LEAN_PROJECT_DEFAULT = str(Path(__file__).resolve().parents[2] / "lean")
BANNED = re.compile(r"\b(?:axiom|sorry|admit|unsafe)\b")
SORRY_WARNING = re.compile(r"declaration uses `sorry`")


def lean_project_dir() -> Path:
    """Resolve the Lean project directory from env, failing loudly if absent."""
    project = Path(os.environ.get("LEAN_PROJECT", LEAN_PROJECT_DEFAULT))
    if not (project / "lakefile.toml").exists():
        raise FileNotFoundError(
            f"Lean project not found at {project}. Set LEAN_PROJECT to the "
            "directory containing lakefile.toml."
        )
    return project


def _module_name(candidate_id: str, run_id: str, candidate_path: Path) -> str:
    """Stable, collision-resistant module name for a candidate.

    The digest covers the candidate CONTENT (plus run and id), so a changed
    candidate gets a fresh module instead of silently resuming a stale proof.
    """
    base = re.sub(r"[^0-9A-Za-z]", "", candidate_id)
    content = hashlib_sha256(candidate_path.read_bytes())[:16]
    digest = hashlib_sha256(f"{run_id}:{candidate_id}:{content}")[:8]
    return f"Formal_{base}_{digest}"


def hashlib_sha256(s: str | bytes) -> str:
    import hashlib
    if isinstance(s, bytes):
        return hashlib.sha256(s).hexdigest()
    return hashlib.sha256(s.encode()).hexdigest()


STAGES = [
    {
        "name": "definitions",
        "desc": ("Write all definitions, the validity predicate, and the theorem/lemma "
                 "STATEMENTS only, with `sorry` placeholders for every proof. "
                 "Run `lake build ThesisLean.<Module>` and make it compile. "
                 "Do NOT yet prove anything."),
        "allow_sorry": True,
        "retries": 2,
    },
    {
        "name": "lemmas",
        "desc": ("Edit the existing module: prove the lemma statements from the "
                 "previous stage with real proofs, removing their `sorry` "
                 "placeholders. Keep the main theorem statement as `sorry` for now. "
                 "Run `lake build ThesisLean.<Module>` and make it compile. "
                 "Before finishing, run `grep -c sorry <the module file>` and "
                 "confirm zero `sorry` remains in the LEMMA section; a build that "
                 "passes with leftover `sorry` is NOT a success."),
        "allow_sorry": True,
        "retries": 6,
    },
    {
        "name": "theorem",
        "desc": ("Edit the existing module: prove the main correctness theorem, "
                 "removing the last `sorry` placeholder(s). Run "
                 "`lake build ThesisLean.<Module>` and make it compile with NO "
                 "`sorry`/`axiom`/`admit`/`unsafe` anywhere. Before finishing, "
                 "run `grep -c sorry <the module file>` and confirm it outputs 0; "
                 "if any `sorry` remains the stage is NOT complete."),
        "allow_sorry": False,
        "retries": 4,
    },
]


def _build_stage_task(
    stage: dict[str, Any],
    stage_index: int,
    problem_name: str,
    candidate_id: str,
    candidate_path: Path,
    module_name: str,
    project_dir: Path,
    retry: int = 0,
    broken_existing: bool = False,
    hints: str = "",
) -> str:
    """Build the stage-specific task for the lean-prover agent."""
    allow = (
        "Development-time `sorry` scaffolding is allowed in this stage, BUT the "
        "final committed module must contain zero sorry/axiom/admit/unsafe."
        if stage["allow_sorry"]
        else "The module must contain ZERO sorry/axiom/admit/unsafe anywhere in "
             "this stage. If a lemma resists proof, report the gap in your final "
             "message instead of leaving sorry."
    )
    resume = (
        f"\nThis is retry {retry + 1} of this stage. The module already contains\n"
        f"work from previous attempts. PRESERVE everything already correct;\n"
        f"only add/complete what this stage requires. Do NOT rewrite the file\n"
        f"from scratch."
        if retry > 0
        else ""
    )
    broken = (
        f"\nThe existing module does not compile and must be rewritten from\n"
        f"scratch; do not preserve its content.\n"
        if broken_existing
        else ""
    )
    hints_text = (
        f"\nProof-strategy hints from the supervisor:\n{hints}\n"
        if hints
        else ""
    )
    return (
        f"Stage {stage_index}/{len(STAGES)}: {stage['name']}\n"
        f"Problem: {problem_name}\n"
        f"Candidate: {candidate_id}\n"
        f"Read the candidate source at {candidate_path} and the problem\n"
        f"definition in the dynamic-graph-algorithms skill.\n"
        f"{stage['desc']}\n"
        f"{resume}"
        f"{broken}"
        f"{hints_text}"
        f"Work in the module {project_dir}/ThesisLean/{module_name}.lean\n"
        f"(create it if it does not exist; the previous stages may have written\n"
        f"it already - edit in place). Ensure `import ThesisLean.{module_name}` is\n"
        f"in {project_dir}/ThesisLean.lean and `cd {project_dir} && lake build\n"
        f"ThesisLean.{module_name}` succeeds for your stage.\n"
        f"Prove the candidate maintains its invariant under every insert/delete\n"
        f"update. The proof must be general (all finite graphs, all legal updates).\n"
        f"{allow}\n"
        f"Report: what you wrote or changed, the theorem statements now proven\n"
        f"(verbatim), the lake build result, and any gaps."
    )


def _dispatch_agent(
    opencode: str,
    run_dir: Path,
    task: str,
    model: str | None,
    timeout: int = 900,
) -> tuple[int, str, str | None]:
    """Dispatch one opencode agent invocation.

    Returns (returncode, output, error_message).
    """
    cmd = [opencode, "run", "--agent", "lean-prover", "--dir", str(run_dir)]
    if model:
        cmd.extend(["-m", model])
    cmd.append(task)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              env=harness_env("opencode"))
        return proc.returncode, proc.stdout + "\n" + proc.stderr, None
    except FileNotFoundError:
        return -1, "", f"opencode binary not found at {opencode}"
    except subprocess.TimeoutExpired:
        return -1, "", f"opencode agent timed out after {timeout}s"
    except Exception as e:  # noqa: BLE001 - record any dispatch failure
        return -1, "", f"agent dispatch failed: {e}"


def _verify_leanchecker(project_dir: Path, module_name: str) -> tuple[bool, str]:
    """Run the independent external kernel checker (Lean4Lean leanchecker) on
    the compiled module. This guards against elaborator/kernel discrepancies
    beyond what `lake build` verifies."""
    cmd = ["lake", "env", "leanchecker", f"ThesisLean.{module_name}"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except FileNotFoundError:
        return False, "leanchecker binary not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "leanchecker timed out after 1800s"
    out = proc.stdout + "\n" + proc.stderr
    ok = proc.returncode == 0
    return ok, out[-3000:]


def _verify_lake_build(project_dir: Path, module_name: str) -> tuple[bool, str]:
    """Run lake build for the module; return (ok, tail_of_output)."""
    cmd = ["lake", "build", f"ThesisLean.{module_name}"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except FileNotFoundError:
        return False, "lake binary not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "lake build timed out after 1800s"
    out = proc.stdout + "\n" + proc.stderr
    ok = proc.returncode == 0 and "Build completed successfully" in out
    if ok:
        # Independent kernel re-check: if leanchecker rejects the module, the
        # build result does not count as verified.
        checker_ok, checker_tail = _verify_leanchecker(project_dir, module_name)
        if not checker_ok:
            return False, "leanchecker rejected module:\n" + checker_tail
    return ok, out[-3000:]


def _verify_lean_no_sorry(project_dir: Path, module_path: Path) -> tuple[bool, str]:
    """Run lean on the module; fail if it reports a `sorry` warning."""
    cmd = ["lake", "env", "lean", str(module_path)]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except FileNotFoundError:
        return False, "lake/lean binary not found on PATH"
    except subprocess.TimeoutExpired:
        return False, "lean timed out"
    out = proc.stdout + "\n" + proc.stderr
    if SORRY_WARNING.search(out):
        return False, out[-2000:]
    return True, out[-2000:]


THEOREM_DECL = re.compile(r"^theorem\s")


def _has_theorem(file_path: Path) -> bool:
    """True if the module declares at least one top-level `theorem`.

    Guards against a truncated/empty module passing the no-banned + no-sorry
    checks: an empty file compiles, emits no sorry warning, and contains no
    banned tokens, yet proves nothing.
    """
    try:
        lines = file_path.read_text().splitlines()
    except OSError:
        return False
    depth = 0
    for line in lines:
        stripped = line.strip()
        if depth > 0:
            depth += stripped.count("/-") - stripped.count("-/")
            if depth < 0:
                depth = 0
            continue
        if stripped.startswith("--"):
            continue
        if stripped.startswith("/-"):
            depth = stripped.count("/-") - stripped.count("-/")
            continue
        if THEOREM_DECL.match(stripped):
            return True
    return False


def _scan_for_banned(file_path: Path) -> list[str]:
    """Return banned-construct occurrences (axiom/sorry/admit/unsafe) outside comments.

    Handles `--` line comments (including trailing ones after code), `/- ... -/`
    block comments, and nested block comments (Lean supports nesting). Counts
    each construct, not each line, so two `sorry` on one line count twice.
    """
    hits: list[str] = []
    try:
        lines = file_path.read_text().splitlines()
    except OSError:
        return ["<unreadable>"]
    depth = 0
    for i, line in enumerate(lines, 1):
        code = line
        stripped = line.strip()
        if depth > 0:
            depth += stripped.count("/-") - stripped.count("-/")
            if depth < 0:
                depth = 0
            continue
        if stripped.startswith("--"):
            continue
        if stripped.startswith("/-"):
            depth = stripped.count("/-") - stripped.count("-/")
            continue
        # strip a trailing `--` line comment so code like `... := trivial -- no sorry`
        # is not counted; only the code part before `--` matters.
        code = line.split("--", 1)[0]
        for m in BANNED.finditer(code):
            hits.append(f"{i}: {m.group(0)}")
    return hits


def _write_result(
    run_dir: Path,
    candidate_id: str,
    result: dict[str, Any],
) -> Path:
    """Atomically write the result JSON."""
    out_dir = run_dir / "formalization"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{candidate_id}.json"
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    tmp.replace(out_path)
    return out_path


def run_formalize(
    run_dir: Path,
    candidate_id: str,
    model: str | None = None,
    opencode_path: str | None = None,
    fresh: bool = False,
    stage_timeout: int = 900,
    hints_path: str | None = None,
) -> int:
    """Execute the formalization workflow for one candidate.

    Returns 0 on success (proof accepted), 1 on failure/rejection, 2 on skip.
    """
    run_dir = Path(run_dir)
    config_path = run_dir / "config.yaml"
    if not config_path.exists():
        print(f"No config found at {config_path}")
        return 2
    config = RunConfig.load(config_path)

    candidate_path = run_dir / "candidates" / f"{candidate_id}.py"
    if not candidate_path.exists():
        print(f"Candidate not found: {candidate_path}")
        return 2

    committed = run_dir / "COMMITTED"
    data = None
    try:
        if committed.exists():
            gen_file = run_dir / f"generation_{int(committed.read_text().strip()):04d}.json"
            if gen_file.exists():
                data = json.loads(gen_file.read_text())
    except (ValueError, json.JSONDecodeError):
        data = None
    if data is None:
        print(f"No committed generation found in {run_dir}; skipping.")
        return 2
    passed = any(
        c.get("id") == candidate_id and c.get("state") == "PASS"
        for c in data.get("candidates", [])
    )
    if not passed:
        print(f"Candidate {candidate_id} is not PASS in the latest generation; skipping.")
        return 2

    try:
        project_dir = lean_project_dir()
    except FileNotFoundError as e:
        print(str(e))
        return 2

    module_name = _module_name(candidate_id, run_dir.name, candidate_path)
    module_path = project_dir / "ThesisLean" / f"{module_name}.lean"

    print(f"Formalizing {candidate_id} ({config.problem}) -> {module_name}")

    # Resume support: if the module already exists and builds, skip definitions.
    existing_build_ok, _ = _verify_lake_build(project_dir, module_name) \
        if module_path.exists() else (False, "")

    # Early-accept branch: an already-complete module skips all agent stages.
    already_complete = (
        module_path.exists()
        and existing_build_ok
        and bool(_verify_lean_no_sorry(project_dir, module_path)[0])
        and not _scan_for_banned(module_path)
    )

    opencode = OpencodeBackend.find_bin(opencode_path)
    resolved_model = model or config.model

    candidate_digest = hashlib_sha256(candidate_path.read_bytes())[:16]

    hints_text = ""
    if hints_path:
        hp = Path(hints_path)
        if hp.exists():
            hints_text = hp.read_text()
        else:
            print(f"  WARNING: hints file not found: {hp}")

    stage_records: list[dict[str, Any]] = []
    total_elapsed = 0.0
    failed_stage: str | None = None
    resumed = False
    if already_complete and not fresh:
        print("  Module already complete (builds, no sorry, no banned); accepting without agent calls.")
        ok_build, build_tail = _verify_lake_build(project_dir, module_name)
        ok_no_sorry, lean_tail = _verify_lean_no_sorry(project_dir, module_path)
        banned = _scan_for_banned(module_path)
        accepted = ok_build and ok_no_sorry and not banned and _has_theorem(module_path)
        result = {
            "candidate_id": candidate_id,
            "problem": config.problem,
            "module": module_name,
            "module_path": str(module_path),
            "model": resolved_model,
            "stages": [],
            "failed_stage": None,
            "already_complete": True,
            "elapsed_seconds": 0.0,
            "build_ok": ok_build,
            "no_sorry_warnings": ok_no_sorry,
            "banned_hits": banned,
            "accepted": accepted,
            "candidate_digest": candidate_digest,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "build_tail": build_tail,
            "lean_tail": lean_tail,
        }
        out_path = _write_result(run_dir, candidate_id, result)
        print(f"  ACCEPTED (already complete) -> {out_path}")
        return 0

    completed_stages: set[str] = set()
    if module_path.exists() and existing_build_ok and not fresh:
        completed_stages.add("definitions")
        resumed = True
        existing_sorries = _scan_for_banned(module_path)
        print(f"  Existing module found and builds ({len(existing_sorries)} "
              f"sorry placeholders remaining); resuming from lemmas stage.")
    elif module_path.exists():
        print(f"  Existing module found but does NOT build; will redo from definitions.")
    for i, stage in enumerate(STAGES, 1):
        if stage["name"] in completed_stages:
            print(f"  Stage {i}/{len(STAGES)} ({stage['name']}): already done, skipping.")
            continue
        stage_attempts = stage.get("retries", 0) + 1
        stage_ok = False
        # Stage-level baseline: progress is measured against where the stage
        # started, so a retry that nets back to the original count still fails.
        stage_start_banned = (
            len(_scan_for_banned(module_path)) if module_path.exists() else 0
        )
        for attempt in range(stage_attempts):
            retry_note = f" (attempt {attempt + 1}/{stage_attempts})" if stage_attempts > 1 else ""
            task = _build_stage_task(
                stage,
                i,
                config.problem,
                candidate_id,
                candidate_path,
                module_name,
                project_dir,
                retry=attempt,
                broken_existing=(
                    module_path.exists()
                    and not existing_build_ok
                    and stage["name"] == "definitions"
                    and attempt == 0
                ),
                hints=hints_text,
            )
            print(f"  Stage {i}/{len(STAGES)} ({stage['name']}){retry_note}...")
            banned_before = len(_scan_for_banned(module_path)) if module_path.exists() else 0
            t0 = time.time()
            returncode, report, agent_exc = _dispatch_agent(
                opencode, run_dir, task, resolved_model, timeout=stage_timeout
            )
            elapsed = time.time() - t0
            total_elapsed += elapsed
            stage_build_ok, stage_build_tail = _verify_lake_build(project_dir, module_name)
            module_present = module_path.exists()
            banned_after = len(_scan_for_banned(module_path)) if module_present else 0
            stage_records.append({
                "stage": stage["name"],
                "attempt": attempt + 1,
                "elapsed_seconds": round(elapsed, 1),
                "agent_return": returncode,
                "agent_error": agent_exc,
                "build_ok": stage_build_ok,
                "banned_before": banned_before,
                "banned_after": banned_after,
                "build_tail": stage_build_tail[-800:],
                "report_tail": report[-2000:],
            })
            print(f"    elapsed {elapsed:.0f}s, exit {returncode}, build "
                  f"{'OK' if stage_build_ok else 'FAILED'}, banned "
                  f"{banned_before} -> {banned_after}"
                  + (f" ({agent_exc})" if agent_exc else ""))
            # Honest-progress gates: a green build is not enough, because `sorry`
            # compiles. The lemmas stage must strictly reduce the stage's starting
            # placeholder count (or the theorem stage inherits fake lemmas it can
            # never discharge); the theorem stage must reach zero. Progress is
            # measured against stage_start_banned so a retry that nets back to the
            # original count still fails.
            if not module_present:
                print("    module missing after attempt; treating as failure")
            elif agent_exc is not None or returncode != 0 or not stage_build_ok:
                pass
            elif stage["name"] == "lemmas" and stage_start_banned > 0 and banned_after >= stage_start_banned:
                print(f"    no sorry removed (stage start {stage_start_banned} -> "
                      f"{banned_after}); treating as failure")
            elif stage["name"] == "theorem" and banned_after != 0:
                print(f"    {banned_after} sorry still present; treating as failure")
            else:
                stage_ok = True
                break
        if not stage_ok:
            failed_stage = stage["name"]
            break

    # After an early failure, skip the expensive final checks: acceptance is
    # already impossible, and the on-disk module may be stale. Keep the cheap
    # banned scan for diagnostics.
    if failed_stage is None:
        ok_build, build_tail = _verify_lake_build(project_dir, module_name)
        ok_no_sorry, lean_tail = _verify_lean_no_sorry(project_dir, module_path) \
            if module_path.exists() else (False, "<module not written>")
    else:
        ok_build, ok_no_sorry = False, False
        build_tail = f"<skipped: stage '{failed_stage}' failed>"
        lean_tail = "<skipped>"
    banned = _scan_for_banned(module_path) if module_path.exists() else ["<module not written>"]

    accepted = (
        failed_stage is None
        and ok_build
        and ok_no_sorry
        and not banned
        and module_path.exists()
        and _has_theorem(module_path)
    )
    result = {
        "candidate_id": candidate_id,
        "problem": config.problem,
        "module": module_name,
        "module_path": str(module_path),
        "model": resolved_model,
        "stages": stage_records,
        "failed_stage": failed_stage,
        "resumed": resumed,
        "candidate_digest": candidate_digest,
        "elapsed_seconds": round(total_elapsed, 1),
        "build_ok": ok_build,
        "no_sorry_warnings": ok_no_sorry,
        "banned_hits": banned,
        "accepted": accepted,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "build_tail": build_tail,
        "lean_tail": lean_tail,
    }
    out_path = _write_result(run_dir, candidate_id, result)

    print(f"  total: {total_elapsed:.0f}s across {len(stage_records)} stage(s)"
          + (f"; failed at {failed_stage}" if failed_stage else ""))
    print(f"  lake build: {'OK' if ok_build else 'FAILED'}")
    print(f"  no sorry warnings: {'OK' if ok_no_sorry else 'FAILED'}")
    print(f"  banned constructs: {banned if banned else 'none'}")
    print(f"  {'ACCEPTED' if accepted else 'REJECTED'} -> {out_path}")
    return 0 if accepted else 1