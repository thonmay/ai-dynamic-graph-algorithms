# AI-assisted code: generated and revised with Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Problem packs: generic, researcher-defined problem specifications.

A problem pack is a folder (by convention under ``problems/<name>/``) that
describes one research problem for the evolutionary loop:

- ``problem.yaml`` (required) - machine-readable spec: which built-in checker
  verifies the candidate (or a custom oracle), graph mode flags, difficulty
  tier, objective, and allowed update modes.
- ``brief.md`` (required) - plain-language research question and hints for the
  agents. Included verbatim in the problem prompt under a RESEARCH BRIEF
  heading, so the tooling itself stays generic.
- ``oracle.py`` (optional) - required when ``checker: oracle``. Must define
  ``offline_compute(graph, root)`` and ``check(state, graph, root) -> bool``.
- ``known_good.py`` (optional) - a reference candidate for self-tests.
- ``faults/`` (optional) - known-bad mutations for self-tests.

The pack is the unit of portability: a researcher adds a folder to describe a
new problem without touching the engine. Built-in checkers are the keys of
``problem_definitions.PROBLEMS``; ``checker: oracle`` defers verification to
the pack's own oracle module.
"""

from __future__ import annotations

import importlib.util
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from .problem_definitions import PROBLEMS, get_problem

#: Default location of the shipped packs, relative to this file:
#: src/evoalgo/packs.py -> repo root -> problems/
DEFAULT_PROBLEMS_ROOT = Path(__file__).resolve().parent.parent.parent / "problems"

#: Keys accepted in problem.yaml. Unknown keys are rejected with a clear
#: message so typos do not silently change behaviour.
KNOWN_KEYS = {
    "name", "title", "directed", "needs_root", "checker",
    "tier", "objective", "update_mode", "lean",
}
VALID_TIERS = {"calibration", "core", "open"}
VALID_UPDATE_MODES = {"mixed", "insert_only", "delete_only"}
VALID_OBJECTIVE_PRIMARY = {"correctness"}
VALID_OBJECTIVE_THEN = {"efficiency", "none"}


class PackError(ValueError):
    """A problem pack failed validation. ``errors`` holds every problem found."""

    def __init__(self, pack_name: str, errors: list[str]):
        self.pack_name = pack_name
        self.errors = list(errors)
        super().__init__(f"problem pack '{pack_name}' is invalid:\n  " + "\n  ".join(self.errors))


@dataclass
class Pack:
    """A validated problem pack."""

    name: str
    title: str
    directed: bool
    needs_root: bool
    checker: str
    tier: str
    objective: dict[str, str]
    update_mode: str
    lean: bool
    brief: str
    path: Path

    @property
    def is_oracle(self) -> bool:
        return self.checker == "oracle"

    def problem_for(self):
        """Return a ProblemDefinition for built-in checkers.

        Raises NotImplementedError for ``checker: oracle`` packs (see
        ``load_pack``): the verifier/sandbox pipeline needs more than the
        oracle's two functions, so full oracle-pack support is planned.
        """
        if self.is_oracle:
            raise NotImplementedError(
                f"custom oracle packs: planned (pack '{self.name}' uses checker: oracle)"
            )
        return get_problem(self.checker)


def _load_problem_yaml(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.exists():
        errors.append("problem.yaml is missing")
        return {}
    if yaml is None:
        errors.append("PyYAML is required to load problem.yaml (pip install pyyaml)")
        return {}
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        errors.append(f"problem.yaml is not valid YAML: {e}")
        return {}
    if not isinstance(data, dict):
        errors.append("problem.yaml must contain a mapping at the top level")
        return {}
    return data


def _validate_pack(data: dict[str, Any], path: Path, errors: list[str]) -> None:
    """Collect every validation problem with ``data`` into ``errors``."""
    unknown = sorted(set(data) - KNOWN_KEYS)
    if unknown:
        errors.append(
            "unknown key(s) in problem.yaml: " + ", ".join(unknown)
            + f" (allowed: {', '.join(sorted(KNOWN_KEYS))})"
        )

    name = data.get("name")
    if not isinstance(name, str) or not name:
        errors.append("'name' is required and must be a non-empty string")
    elif name != path.name:
        errors.append(f"'name' ({name!r}) must match the pack folder name ({path.name!r})")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("'title' is required and must be a non-empty string")

    directed = data.get("directed")
    if not isinstance(directed, bool):
        errors.append("'directed' is required and must be a boolean")
    needs_root = data.get("needs_root")
    if not isinstance(needs_root, bool):
        errors.append("'needs_root' is required and must be a boolean")

    checker = data.get("checker")
    if not isinstance(checker, str) or not checker:
        errors.append("'checker' is required (a built-in checker name, or 'oracle')")
    elif checker == "oracle":
        oracle_path = path / "oracle.py"
        if not oracle_path.exists():
            errors.append("checker is 'oracle' but oracle.py is missing")
        else:
            _validate_oracle(oracle_path, errors)
    elif checker not in PROBLEMS:
        errors.append(
            f"unknown checker {checker!r}; must be one of "
            f"{sorted(PROBLEMS)} or 'oracle'"
        )

    tier = data.get("tier")
    if tier not in VALID_TIERS:
        errors.append(f"'tier' must be one of {sorted(VALID_TIERS)}, got {tier!r}")

    objective = data.get("objective", {"primary": "correctness", "then": "efficiency"})
    if not isinstance(objective, dict):
        errors.append("'objective' must be a mapping with keys 'primary' and 'then'")
    else:
        if objective.get("primary") not in VALID_OBJECTIVE_PRIMARY:
            errors.append(
                f"objective.primary must be one of {sorted(VALID_OBJECTIVE_PRIMARY)}, "
                f"got {objective.get('primary')!r}"
            )
        if objective.get("then") not in VALID_OBJECTIVE_THEN:
            errors.append(
                f"objective.then must be one of {sorted(VALID_OBJECTIVE_THEN)}, "
                f"got {objective.get('then')!r}"
            )

    update_mode = data.get("update_mode", "mixed")
    if update_mode not in VALID_UPDATE_MODES:
        errors.append(
            f"'update_mode' must be one of {sorted(VALID_UPDATE_MODES)}, got {update_mode!r}"
        )

    lean = data.get("lean", {"enabled": False})
    if lean is None:
        lean = {"enabled": False}
    if not isinstance(lean, dict) or not isinstance(lean.get("enabled", False), bool):
        errors.append("'lean' must be a mapping with a boolean 'enabled' key")

    brief_path = path / "brief.md"
    if not brief_path.exists():
        errors.append("brief.md is missing (required: plain-language research question)")
    elif not brief_path.read_text().strip():
        errors.append("brief.md is empty (required: plain-language research question)")

    # Flag consistency: a built-in checker fixes directed/needs_root, and the
    # pack must not contradict it.
    if (
        isinstance(checker, str)
        and checker in PROBLEMS
        and isinstance(directed, bool)
        and isinstance(needs_root, bool)
    ):
        try:
            ref = get_problem(checker)
        except ValueError:
            ref = None
        if ref is not None:
            if directed != ref.directed:
                errors.append(
                    f"'directed' is {directed} but checker {checker!r} is "
                    f"{'directed' if ref.directed else 'undirected'}"
                )
            if needs_root != ref.needs_root:
                errors.append(
                    f"'needs_root' is {needs_root} but checker {checker!r} "
                    f"{'needs' if ref.needs_root else 'does not need'} a root"
                )


def _validate_oracle(oracle_path: Path, errors: list[str]) -> None:
    """Validate the oracle.py interface: offline_compute(graph, root),
    check(state, graph, root) -> bool."""
    try:
        spec = importlib.util.spec_from_file_location("pack_oracle", oracle_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        errors.append(f"oracle.py failed to import: {e}")
        return
    # offline_compute(graph, root) -> 2 params; check(state, graph, root) -> 3.
    expected_arity = {"offline_compute": 2, "check": 3}
    for fn_name, arity in expected_arity.items():
        fn = getattr(module, fn_name, None)
        if fn is None or not callable(fn):
            errors.append(f"oracle.py must define a callable {fn_name}(...)")
            continue
        try:
            params = list(inspect.signature(fn).parameters)
        except (TypeError, ValueError):
            params = []
        if len(params) < arity:
            errors.append(
                f"oracle.py {fn_name} must take "
                f"{'(graph, root)' if arity == 2 else '(state, graph, root)'}; "
                f"got parameters {params}"
            )


def load_pack(path: Path | str) -> Pack:
    """Load and validate one problem pack from ``path`` (a directory).

    Raises PackError listing every problem found, or NotImplementedError for
    ``checker: oracle`` packs (interface validated; full support planned).
    """
    path = Path(path)
    errors: list[str] = []
    if not path.is_dir():
        raise PackError(str(path), [f"not a directory: {path}"])

    data = _load_problem_yaml(path / "problem.yaml", errors)
    if data:
        _validate_pack(data, path, errors)
    if errors:
        raise PackError(data.get("name") or path.name, errors)

    brief = (path / "brief.md").read_text()
    if data.get("checker") == "oracle":
        # The oracle interface is validated above. Building a full
        # ProblemDefinition from oracle.py is not generically possible: the
        # verifier/sandbox pipeline also needs extract_result, baseline_work,
        # offline_source, and failing_context, which are problem-specific.
        # TODO: support custom oracle packs (wrap the oracle in a
        # ProblemDefinition subclass with generic extract/failing_context).
        raise NotImplementedError(
            "custom oracle packs: planned "
            f"(pack '{data['name']}' declares checker: oracle with a valid oracle.py)"
        )

    return Pack(
        name=data["name"],
        title=data["title"],
        directed=data["directed"],
        needs_root=data["needs_root"],
        checker=data["checker"],
        tier=data["tier"],
        objective=data.get("objective", {"primary": "correctness", "then": "efficiency"}),
        update_mode=data.get("update_mode", "mixed"),
        lean=bool(data.get("lean", {}).get("enabled", False)),
        brief=brief,
        path=path,
    )


def find_packs(root: Path | str = DEFAULT_PROBLEMS_ROOT) -> list[Pack]:
    """Find every loadable pack under ``root`` (one per subdirectory).

    Invalid packs are skipped (their errors are not raised here); use
    ``load_pack`` on a specific directory to see them.
    """
    root = Path(root)
    packs: list[Pack] = []
    if not root.is_dir():
        return packs
    for sub in sorted(root.iterdir()):
        if not sub.is_dir() or not (sub / "problem.yaml").exists():
            continue
        try:
            packs.append(load_pack(sub))
        except (PackError, NotImplementedError):
            continue
    return packs


def resolve_pack(name_or_path: str | Path, root: Path | str = DEFAULT_PROBLEMS_ROOT) -> Pack:
    """Resolve a pack by name (looked up under ``root``) or by path.

    Raises PackError if it cannot be found, or NotImplementedError for
    oracle packs (see load_pack).
    """
    p = Path(name_or_path)
    if p.is_dir() and (p / "problem.yaml").exists():
        return load_pack(p)
    candidate = Path(root) / name_or_path
    if candidate.is_dir():
        return load_pack(candidate)
    raise PackError(
        str(name_or_path),
        [f"no problem pack found: looked for directory '{p}' and '{candidate}'"],
    )


def pack_info(pack: Pack) -> dict[str, Any]:
    # The "Research question:" paragraph, joined across its wrapped lines.
    question = None
    for para in pack.brief.split("\n\n"):
        if para.strip().lower().startswith("research question"):
            question = " ".join(para.split(":", 1)[1].split())
            break
    return {
        "name": pack.name, "title": pack.title, "tier": pack.tier,
        "directed": pack.directed, "needs_root": pack.needs_root, "checker": pack.checker,
        "update_mode": pack.update_mode, "lean": pack.lean, "objective": pack.objective,
        "question": question, "brief": pack.brief,
    }
