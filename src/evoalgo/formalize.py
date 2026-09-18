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

from .config import RunConfig

logger = logging.getLogger(__name__)

LEAN_PROJECT_DEFAULT = "/proj/MPS/MPS_DEV_REPO/ethomdt/thesis-lean"
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


def _module_name(candidate_id: str, run_id: str) -> str:
    """Stable, collision-resistant module name for a candidate."""
    base = re.sub(r"[^0-9A-Za-z]", "", candidate_id)
    digest = hashlib_sha256(f"{run_id}:{candidate_id}")[:8]
    return f"Formal_{base}_{digest}"


def hashlib_sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()


def _build_task(
    problem_name: str,
    candidate_id: str,
    candidate_path: Path,
    module_name: str,
    project_dir: Path,
) -> str:
    """Build the formalization task for the lean-prover agent."""
    return (
        f"Problem: {problem_name}\n"
        f"Candidate: {candidate_id}\n"
        f"Read the candidate source at {candidate_path} and the problem\n"
        f"definition in the dynamic-graph-algorithms skill.\n"
        f"Write the proof module to {project_dir}/ThesisLean/{module_name}.lean\n"
        f"and add `import ThesisLean.{module_name}` to {project_dir}/ThesisLean.lean\n"
        f"(create both edits; the module file may not already exist).\n"
        f"Run `cd {project_dir} && lake build ThesisLean.{module_name}` until it succeeds.\n"
        f"Prove the candidate maintains its invariant under every insert/delete update.\n"
        f"The proof must be general (all finite graphs, all legal updates), with no\n"
        f"axiom, sorry, admit, or unsafe anywhere. If a lemma resists proof, report\n"
        f"the gap in your final message instead of leaving sorry.\n"
        f"Report: modules written, the theorem statements proved (verbatim), the\n"
        f"lake build result, and any gaps."
    )


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


def _scan_for_banned(file_path: Path) -> list[str]:
    """Return lines containing axiom/sorry/admit/unsafe outside comments/docstrings.

    Handles `--` line comments and `/- ... -/` block comments, including nested
    block comments (Lean supports nesting).
    """
    hits: list[str] = []
    try:
        lines = file_path.read_text().splitlines()
    except OSError:
        return ["<unreadable>"]
    depth = 0
    for i, line in enumerate(lines, 1):
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
        if BANNED.search(line):
            hits.append(f"{i}: {line.strip()[:120]}")
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
    enlcode_path: str | None = None,
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

    module_name = _module_name(candidate_id, run_dir.name)
    module_path = project_dir / "ThesisLean" / f"{module_name}.lean"
    if module_path.exists():
        print(f"Module {module_name} already exists at {module_path}; refusing to overwrite.")
        return 1

    task = _build_task(
        config.problem,
        candidate_id,
        candidate_path,
        module_name,
        project_dir,
    )

    print(f"Formalizing {candidate_id} ({config.problem}) -> {module_name}")

    enlcode = enlcode_path or os.environ.get(
        "ENLCODE_PATH", str(Path.home() / ".enlcode" / "enlcode")
    )
    cmd = [enlcode, "run", "--agent", "lean-prover",
           "--dir", str(run_dir)]
    if model or config.model:
        cmd.extend(["-m", model or config.model])
    cmd.append(task)

    t0 = time.time()
    agent_exc = None
    report = ""
    returncode = -1
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        returncode = proc.returncode
        report = proc.stdout + "\n" + proc.stderr
    except FileNotFoundError:
        agent_exc = f"enlcode binary not found at {enlcode}"
    except subprocess.TimeoutExpired:
        agent_exc = "enlcode agent timed out after 7200s"
    except Exception as e:  # noqa: BLE001 - record any dispatch failure
        agent_exc = f"agent dispatch failed: {e}"
    elapsed = time.time() - t0

    ok_build, build_tail = _verify_lake_build(project_dir, module_name)
    ok_no_sorry, lean_tail = _verify_lean_no_sorry(project_dir, module_path) \
        if module_path.exists() else (False, "<module not written>")
    banned = _scan_for_banned(module_path) if module_path.exists() else ["<module not written>"]

    accepted = (
        agent_exc is None
        and returncode == 0
        and ok_build
        and ok_no_sorry
        and not banned
        and module_path.exists()
    )
    result = {
        "candidate_id": candidate_id,
        "problem": config.problem,
        "module": module_name,
        "module_path": str(module_path),
        "model": model or config.model,
        "agent_return": returncode,
        "agent_error": agent_exc,
        "elapsed_seconds": round(elapsed, 1),
        "build_ok": ok_build,
        "no_sorry_warnings": ok_no_sorry,
        "banned_hits": banned,
        "accepted": accepted,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "agent_report_tail": report[-4000:],
        "build_tail": build_tail,
        "lean_tail": lean_tail,
    }
    out_path = _write_result(run_dir, candidate_id, result)

    print(f"  Agent: {'error: ' + agent_exc if agent_exc else f'elapsed {elapsed:.0f}s, exit {returncode}'}")
    print(f"  lake build: {'OK' if ok_build else 'FAILED'}")
    print(f"  no sorry warnings: {'OK' if ok_no_sorry else 'FAILED'}")
    print(f"  banned constructs: {banned if banned else 'none'}")
    print(f"  {'ACCEPTED' if accepted else 'REJECTED'} -> {out_path}")
    return 0 if accepted else 1