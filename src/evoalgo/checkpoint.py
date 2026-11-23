# AI-assisted code: generated and revised with GLM-5.2
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Atomic checkpoint persistence for generation state.

``commit`` writes generation_NNNN.json (temp file + rename) and then the
COMMITTED marker; loading verifies the schema version and SHA-256 checksum.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from .candidate import Candidate

SCHEMA_VERSION = 2


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)


class Checkpoint:
    """Manages atomic generation persistence in a run directory."""

    def __init__(self, run_dir: Path | str):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "candidates").mkdir(exist_ok=True)
        (self.run_dir / "reflections").mkdir(exist_ok=True)
        (self.run_dir / "dashboard").mkdir(exist_ok=True)
        (self.run_dir / "results").mkdir(exist_ok=True)

    def _gen_path(self, generation: int) -> Path:
        return self.run_dir / f"generation_{generation:04d}.json"

    def commit(
        self,
        generation: int,
        run_id: str,
        problem: str,
        bound: dict[str, Any],
        candidates: list[Candidate],
        config_ref: str = "config.yaml",
        model_calls: int = 0,
        consecutive_all_failed: int = 0,
        fitness_history: list[float] | None = None,
        stop_reason: str | None = None,
    ) -> Path:
        """Atomically write a generation state file.

        Writes to a temp file, then os.replace (atomic on POSIX),
        then updates the COMMITTED marker.
        """
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "generation": generation,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "problem": problem,
            "bound": bound,
            "config_ref": config_ref,
            "candidates": [c.to_json() for c in candidates],
            "model_calls": model_calls,
            "consecutive_all_failed": consecutive_all_failed,
            "fitness_history": fitness_history or [],
            "stop_reason": stop_reason,
        }
        # Compute checksum over the payload without the checksum field
        canonical = _canonical_json(payload).encode()
        checksum = _sha256(canonical)
        payload["checksum"] = f"sha256:{checksum}"

        target = self._gen_path(generation)
        tmp = target.with_suffix(".tmp")

        content = json.dumps(payload, indent=2, ensure_ascii=False)
        tmp.write_text(content)
        os.replace(tmp, target)  # atomic on POSIX

        committed_path = self.run_dir / "COMMITTED"
        committed_path.write_text(str(generation))

        return target

    def load_generation(self, generation: int) -> dict[str, Any] | None:
        """Load a specific generation file, verifying checksum."""
        path = self._gen_path(generation)
        if not path.exists():
            return None
        return self._load_and_verify(path)

    def load_latest(self) -> dict[str, Any] | None:
        """Load the last committed generation, or None if no commits."""
        committed_path = self.run_dir / "COMMITTED"
        if not committed_path.exists():
            return None
        return self.load_generation(self.latest_generation_number())

    def latest_generation_number(self) -> int:
        """Return the last committed generation number, or 0 if none."""
        committed_path = self.run_dir / "COMMITTED"
        if not committed_path.exists():
            return 0
        text = committed_path.read_text().strip()
        if not text.isdigit():
            raise ValueError(f"corrupt COMMITTED marker: {text[:40]!r}")
        return int(text)

    def _load_and_verify(self, path: Path) -> dict[str, Any]:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise ValueError(f"{path.name} is not valid JSON: {e}") from None

        sv = data.get("schema_version", 0)
        if sv != SCHEMA_VERSION:
            raise ValueError(
                f"Incompatible schema version {sv} in {path.name} "
                f"(expected {SCHEMA_VERSION})"
            )

        stored_checksum = data.pop("checksum", None)
        if stored_checksum is None:
            raise ValueError(f"Missing checksum in {path.name}")
        expected = stored_checksum.replace("sha256:", "")
        actual = _sha256(_canonical_json(data).encode())
        if expected != actual:
            raise ValueError(
                f"Checksum mismatch in {path.name}: "
                f"expected {expected[:16]}..., got {actual[:16]}..."
            )

        return data

    def list_generations(self) -> list[int]:
        """List all generation numbers that have files (may include incomplete)."""
        gens = []
        for p in self.run_dir.glob("generation_*.json"):
            try:
                num = int(p.stem.split("_")[1])
                gens.append(num)
            except (IndexError, ValueError):
                continue
        return sorted(gens)

    def discard_incomplete(self) -> list[int]:
        """Remove generation files beyond the COMMITTED marker.

        Returns the list of removed generation numbers.
        """
        last_committed = self.latest_generation_number()
        all_gens = self.list_generations()
        removed = []
        for g in all_gens:
            if g > last_committed:
                self._gen_path(g).unlink()
                removed.append(g)
        return removed
