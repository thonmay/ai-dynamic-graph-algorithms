"""Orchestrator: composition root and evolutionary loop driver.

The Orchestrator owns the evolutionary loop:
  1. Select parents (elitism + fitness-proportional)
  2. Generate offspring (LLM provider -> generator agent)
  3. Verify candidates (sandbox + verifier)
  4. Reflect on failures (LLM provider -> reflector agent)
  5. Score (evaluator: fitness, work_ratio)
  6. Select and commit (population cull + checkpoint)

Stop conditions:
  - Any candidate reaches fitness 1.0 (success)
  - Max generations reached
  - Max consecutive all-failed generations
  - Model call budget exhausted
"""

from __future__ import annotations

import json
import logging
import os
import random
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from .candidate import Candidate, CandidateState
from .checkpoint import Checkpoint
from .config import RunConfig
from .dashboard import Dashboard
from .events import (
    ENGINE_FILE,
    STEERABLE_FIELDS,
    ControlChannel,
    EventLog,
    read_events,
    validate_command,
)
from .llm_provider import LLMProvider
from .population import Population
from .problem_definitions import ProblemDefinition, get_problem
from .reflector import Reflector
from .sandbox import Sandbox
from .verifier import Verifier

logger = logging.getLogger(__name__)


class Orchestrator:
    """Composition root. Drives the evolutionary loop."""

    def __init__(self, config: RunConfig, run_id: str | None = None):
        self.config = config
        self.run_id = run_id or self._generate_run_id()
        self.run_dir = Path(config.workdir).resolve() / self.run_id

        # Validate config
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid config: {'; '.join(errors)}")

        # Initialize components. validate() already resolved config.problem
        # from the pack; the pack adds update mode and the optional Lean step.
        self.pack = None
        if config.pack:
            from .packs import resolve_pack
            self.pack = resolve_pack(config.pack)
        self.problem: ProblemDefinition = get_problem(config.problem)
        self.sandbox = Sandbox(timeout_seconds=config.timeout_seconds,
                               directed=self.problem.directed)
        self.verifier = Verifier(
            problem=self.problem,
            sandbox=self.sandbox,
            bound_n_max=config.bound.n_max,
            bound_n_random=config.bound.n_random,
            bound_seq_len_max=config.bound.seq_len_max,
            bound_seq_count=config.bound.seq_count,
            bound_seed=config.bound.seed,
            update_mode=self.pack.update_mode if self.pack else "mixed",
        )
        self.checkpoint = Checkpoint(self.run_dir)
        self.provider = LLMProvider(config=config, run_dir=self.run_dir)
        self.reflector = Reflector(provider=self.provider, problem=self.problem)
        self.dashboard = Dashboard(self.run_dir)
        self.population = Population(
            max_size=config.population_size,
            elitism_k=config.elitism_k,
            diversity_threshold=config.diversity_threshold,
            crossover_enabled=config.crossover_enabled,
        )

        self.generation = 0
        self.consecutive_all_failed = 0
        self.model_calls = 0
        self.stop_reason: str | None = None
        self.fitness_history: list[float] = []

        # Save config
        self.run_dir.mkdir(parents=True, exist_ok=True)
        config.save(self.run_dir / "config.yaml")

        # Event log (monitoring/replay) and control channel (steering)
        self.events = EventLog(self.run_dir)
        self.control = ControlChannel(self.run_dir, self.events)
        self.paused = False

    def _generate_run_id(self) -> str:
        ts = time.strftime("%Y%m%d_%H%M%S")
        rand = random.randint(0, 999)
        return f"run_{ts}_{rand:03d}"

    def run(self) -> dict[str, Any]:
        """Run the evolutionary loop to completion.

        Returns a run summary dict.
        """
        logger.info("Starting run %s (problem=%s, pop=%d, max_gen=%d)",
                     self.run_id, self.config.problem,
                     self.config.population_size, self.config.max_generations)
        self._write_engine_file()
        try:
            return self._run()
        finally:
            self._remove_engine_file()

    def _run(self) -> dict[str, Any]:
        # Try to resume from checkpoint
        loaded = self._try_resume()
        # A hint set before a resume stays in effect.
        for e in read_events(self.run_dir):
            if e.get("type") == "control_ack" and e.get("cmd") == "hint":
                self.provider.hint = (e.get("text") or "").strip() or None
        self.events.emit(
            "run_start", run_id=self.run_id, problem=self.config.problem,
            pack=self.config.pack, research_goal=self.config.research_goal,
            provider=self.config.provider, model=self.config.model,
            population_size=self.config.population_size,
            max_generations=self.config.max_generations,
            model_call_budget=self.config.model_call_budget,
            resumed=loaded, generation=self.generation,
        )
        if not loaded:
            # Seed: generate initial population from scratch
            self._apply_control()
            if not self.stop_reason:
                self._seed_initial_population()

        while self.generation < self.config.max_generations:
            self._apply_control()
            if self.stop_reason:
                break

            self.step_generation()

        # Final export
        summary = self._export_summary()
        self._maybe_formalize(summary)
        self.events.emit(
            "run_end", stop_reason=self.stop_reason, generation=self.generation,
            best_candidate_id=summary["best_candidate_id"],
            best_fitness=summary["best_fitness"],
            best_work_ratio=summary["best_work_ratio"],
            model_calls=self.model_calls,
        )
        return summary

    def _maybe_formalize(self, summary: dict[str, Any]) -> None:
        """Optional final step (pack ``lean: {enabled: true}``): ask the Lean
        prover agent to prove the best correct candidate. Experimental: needs
        the Lean project and an enlcode harness; never fails the run."""
        best = summary.get("best_candidate_id")
        if not (self.pack and self.pack.lean) or self.stop_reason == "user_stop":
            return
        if not best or summary.get("best_fitness") != 1.0:
            self.events.emit("lean_skipped", reason="no fully correct candidate")
            return
        from .formalize import run_formalize
        self.events.emit("lean_start", id=best)
        started = time.monotonic()
        try:
            code = run_formalize(self.run_dir, best, model=self.config.model)
        except Exception as e:  # experimental step must not lose the run
            logger.exception("Lean step failed")
            code, error = 1, str(e)[:500]
        else:
            error = None
        self.events.emit("lean_end", id=best, result={0: "proved", 2: "skipped"}.get(code, "failed"),
                         error=error, duration_s=round(time.monotonic() - started, 1))

    def _apply_control(self) -> None:
        """Control point at a generation boundary."""
        self._control_point(None, self.generation + 1)

    def _before_call(self, gen: int, role: str, cid: str) -> bool:
        """Control point before an agent call. False means the run is stopping."""
        self._control_point({"role": role, "id": cid}, gen)
        return not self.stop_reason

    def _control_point(self, before: dict[str, str] | None, gen: int) -> None:
        """Apply pending commands; block while paused.

        Called before every agent call and at generation boundaries, so a
        pause or stop waits for at most one agent call.
        """
        announced = False
        while True:
            for command in self.control.pending():
                self._handle_command(command)
            if not self.paused or self.stop_reason:
                break
            if not announced:
                self.events.emit("paused", gen=gen, before=before)
                announced = True
            self.control.sleep(self.control.poll_interval)
        if announced and not self.stop_reason:
            self.events.emit("resumed", gen=gen)

    @contextmanager
    def _agent_call(self, gen: int, role: str, cid: str, agent: str,
                    produced: Callable[[], bool]):
        """Emit agent_call_start/end around one provider call."""
        self.events.emit("agent_call_start", gen=gen, role=role, id=cid,
                         agent=agent, model=self.config.model)
        started = time.monotonic()
        try:
            yield
        finally:
            self.events.emit("agent_call_end", gen=gen, role=role, id=cid, ok=bool(produced()),
                             duration_s=round(time.monotonic() - started, 1))

    def _write_engine_file(self) -> None:
        """Record the engine process so the UI can tell a live run from a crashed one."""
        try:
            tmp = self.run_dir / f"{ENGINE_FILE}.tmp"
            tmp.write_text(json.dumps({
                "pid": os.getpid(), "host": socket.gethostname(),
                "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }))
            os.replace(tmp, self.run_dir / ENGINE_FILE)
        except OSError as e:
            logger.warning("Could not write %s: %s", ENGINE_FILE, e)

    def _remove_engine_file(self) -> None:
        try:
            (self.run_dir / ENGINE_FILE).unlink(missing_ok=True)
        except OSError as e:
            logger.warning("Could not remove %s: %s", ENGINE_FILE, e)

    def _handle_command(self, command: dict[str, Any]) -> None:
        error = validate_command(command)
        cmd = command.get("cmd")
        if error is None and cmd == "set" and command["field"] == "population_size" \
                and command["value"] < self.config.elitism_k:
            error = f"population_size cannot be below elitism_k ({self.config.elitism_k})"
        if error is not None:
            self.control.reject(command, self.generation, error)
            return

        if cmd == "pause":
            self.paused = True
        elif cmd == "resume":
            self.paused = False
        elif cmd == "stop":
            self.paused = False
            self.stop_reason = "user_stop"
        elif cmd == "hint":
            # An empty hint clears the current one.
            self.provider.hint = command["text"].strip() or None
        elif cmd == "set":
            field, value = command["field"], command["value"]
            assert field in STEERABLE_FIELDS
            setattr(self.config, field, value)
            if field == "population_size":
                self.population.max_size = value
            # Persist so a later resume continues with the steered value.
            self.config.save(self.run_dir / "config.yaml")
        self.control.ack(command, self.generation)
        logger.info("Control %s applied at generation %d", cmd, self.generation)

    def _emit_candidate(self, candidate: Candidate, role: str) -> None:
        self.events.emit("candidate_generated", id=candidate.id, gen=candidate.generation,
                         parent_ids=candidate.parent_ids, role=role)

    def _emit_verified(self, candidate: Candidate) -> None:
        self.events.emit(
            "candidate_verified", id=candidate.id, gen=candidate.generation,
            state=candidate.state.value, fitness=candidate.fitness,
            work_ratio=candidate.work_ratio, timeout=candidate.timeout,
            tests_passed=candidate.tests_passed, tests_total=candidate.tests_total,
            failing_case=candidate.failing_case,
            error=(candidate.error_message or "")[:500] or None,
        )

    def _reflect(self, candidate: Candidate, gen: int) -> None:
        with self._agent_call(gen, "reflect", candidate.id, self.config.reflector_agent,
                              lambda: candidate.reflection_path is not None):
            self.reflector.reflect(candidate, self.run_dir, gen)
        self.model_calls = self.provider.call_count
        self.events.emit("candidate_reflected", id=candidate.id, gen=gen,
                         reflection_path=candidate.reflection_path)

    def _try_resume(self) -> bool:
        """Try to resume from the last checkpoint. Returns True if resumed."""
        latest = self.checkpoint.load_latest()
        if latest is None:
            return False

        self.generation = latest["generation"]
        self.model_calls = latest.get("model_calls", 0)
        self.consecutive_all_failed = latest.get("consecutive_all_failed", 0)
        self.fitness_history = latest.get("fitness_history", [])
        self.stop_reason = latest.get("stop_reason")

        # If the run stopped due to budget exhaustion but the budget has
        # been raised since, clear the stop reason so the loop can continue.
        if self.stop_reason == "model_call_budget_exhausted":
            if self.model_calls < self.config.model_call_budget:
                logger.info("Budget raised since last stop (%d < %d), resuming",
                            self.model_calls, self.config.model_call_budget)
                self.stop_reason = None
            else:
                logger.info("Budget still exhausted (%d >= %d), nothing to resume",
                            self.model_calls, self.config.model_call_budget)
        self.population = Population.from_json(
            latest["candidates"],
            max_size=self.config.population_size,
            elitism_k=self.config.elitism_k,
            diversity_threshold=self.config.diversity_threshold,
            crossover_enabled=self.config.crossover_enabled,
        )

        # If fitness_history wasn't in the checkpoint, reconstruct it
        if not self.fitness_history:
            for gen_num in range(1, self.generation + 1):
                gen_data = self.checkpoint.load_generation(gen_num)
                if gen_data:
                    candidates = gen_data.get("candidates", [])
                    best = max((c.get("fitness", 0) for c in candidates), default=0)
                    self.fitness_history.append(best)

        logger.info("Resumed from generation %d (%d candidates)",
                     self.generation, self.population.size)
        return True

    def _seed_initial_population(self) -> None:
        """Generate the first batch of candidates from scratch."""
        logger.info("Seeding initial population (size=%d)", self.config.population_size)
        self.generation = 0
        self.events.emit("gen_start", gen=1)

        # Generate N candidates with no parent (fresh). range() is evaluated
        # once, so a population_size change applies from the next generation.
        new_candidates: list[Candidate] = []

        for i in range(self.config.population_size):
            if self.model_calls >= self.config.model_call_budget:
                self.stop_reason = "model_call_budget_exhausted"
                logger.warning("Model call budget exhausted during seeding")
                break

            candidate_id = f"gen{self.generation + 1:03d}_c{i + 1:02d}"
            code_filename = f"{candidate_id}.py"
            code_path = self.run_dir / "candidates" / code_filename
            if not self._before_call(1, "seed", candidate_id):
                break

            # Call generator with no parent
            with self._agent_call(1, "seed", candidate_id, self.config.generator_agent,
                                  code_path.exists):
                self.provider.generate(
                    problem_name=self.config.problem,
                    parent_code=None,
                    candidate_filename=code_filename,
                    generation=self.generation + 1,
                    workdir=str(self.run_dir),
                )
            self.model_calls = self.provider.call_count

            if code_path.exists():
                candidate = Candidate(
                    id=candidate_id,
                    code_path=str(code_path),
                    generation=self.generation + 1,
                    parent_ids=[],
                )
                new_candidates.append(candidate)
                self._emit_candidate(candidate, "seed")
            else:
                logger.warning("Generator did not produce %s", code_path)
                self.events.emit("agent_failed", gen=1, id=candidate_id, role="seed")

        # Verify all new candidates
        for candidate in new_candidates:
            self.verifier.verify(candidate)
            self._emit_verified(candidate)

        # Reflect on failures
        for candidate in new_candidates:
            if candidate.is_failed:
                if self.model_calls >= self.config.model_call_budget:
                    self.stop_reason = "model_call_budget_exhausted"
                    logger.warning("Model call budget exhausted during reflection")
                    break
                if not self._before_call(1, "reflect", candidate.id):
                    break
                self._reflect(candidate, self.generation + 1)

        # Add to population
        for candidate in new_candidates:
            self.population.add(candidate)

        # Commit generation 1
        self.generation = 1
        self._check_stop_conditions()
        self._commit_generation()

    def step_generation(self) -> None:
        """Execute one generation of the evolutionary loop."""
        self.generation += 1
        gen = self.generation
        logger.info("=== Generation %d ===", gen)
        self.events.emit("gen_start", gen=gen)

        new_candidates: list[Candidate] = []

        # Determine how many new candidates to generate
        slots = self.config.population_size - len([
            c for c in self.population.candidates
            if c.state == CandidateState.PASS
        ])

        # Prioritize repair of failed candidates with reflections
        repairable = self.population.get_failed_repairable()
        repair_count = min(len(repairable), slots)
        fresh_count = slots - repair_count

        # Diversity injection: if population is too similar, add a fresh candidate
        if self.population.needs_diversity_injection:
            logger.info("Diversity injection triggered (diversity=%.2f)",
                        self.population.compute_diversity())
            fresh_count += 1

        # Repair phase
        for i in range(repair_count):
            if self.model_calls >= self.config.model_call_budget:
                self.stop_reason = "model_call_budget_exhausted"
                break

            parent = repairable[i]
            candidate_id = f"gen{gen:03d}_c{i + 1:02d}"
            code_filename = f"{candidate_id}.py"

            # Read parent code
            parent_code_path = Path(parent.code_path)
            try:
                parent_code = parent_code_path.read_text()
            except Exception:
                parent_code = ""

            # Read reflection
            reflection_text = ""
            if parent.reflection_path:
                refl_path = Path(parent.reflection_path)
                if not refl_path.is_absolute():
                    refl_path = self.run_dir / parent.reflection_path
                try:
                    reflection_text = refl_path.read_text()
                except Exception:
                    pass

            code_path = self.run_dir / "candidates" / code_filename
            if not self._before_call(gen, "repair", candidate_id):
                break
            with self._agent_call(gen, "repair", candidate_id, self.config.repairer_agent,
                                  code_path.exists):
                self.provider.repair(
                    problem_name=self.config.problem,
                    failed_code=parent_code,
                    reflection=reflection_text,
                    candidate_filename=code_filename,
                    workdir=str(self.run_dir),
                )
            self.model_calls = self.provider.call_count

            if code_path.exists():
                candidate = Candidate(
                    id=candidate_id,
                    code_path=str(code_path),
                    generation=gen,
                    parent_ids=[parent.id],
                )
                new_candidates.append(candidate)
                self._emit_candidate(candidate, "repair")
            else:
                self.events.emit("agent_failed", gen=gen, id=candidate_id, role="repair")

        # Fresh generation phase
        for i in range(fresh_count):
            if self.model_calls >= self.config.model_call_budget:
                self.stop_reason = "model_call_budget_exhausted"
                break

            idx = repair_count + i
            candidate_id = f"gen{gen:03d}_c{idx + 1:02d}"
            code_filename = f"{candidate_id}.py"

            # Select a parent (or None for fresh)
            parents = self.population.select_parents(count=1)
            parent = parents[0] if parents else None

            parent_code = None
            parent_ids: list[str] = []
            if parent is not None:
                parent_code_path = Path(parent.code_path)
                try:
                    parent_code = parent_code_path.read_text()
                    parent_ids = [parent.id]
                except Exception:
                    pass

            role = "mutate" if parent_ids else "fresh"
            code_path = self.run_dir / "candidates" / code_filename
            if not self._before_call(gen, role, candidate_id):
                break
            with self._agent_call(gen, role, candidate_id, self.config.generator_agent,
                                  code_path.exists):
                self.provider.generate(
                    problem_name=self.config.problem,
                    parent_code=parent_code,
                    candidate_filename=code_filename,
                    generation=gen,
                    workdir=str(self.run_dir),
                )
            self.model_calls = self.provider.call_count

            if code_path.exists():
                candidate = Candidate(
                    id=candidate_id,
                    code_path=str(code_path),
                    generation=gen,
                    parent_ids=parent_ids,
                )
                new_candidates.append(candidate)
                self._emit_candidate(candidate, "mutate" if parent_ids else "fresh")
            else:
                self.events.emit("agent_failed", gen=gen, id=candidate_id,
                                 role="mutate" if parent_ids else "fresh")

        if not new_candidates:
            logger.warning("Generation %d produced no candidates", gen)
            self._check_stop_conditions()
            self._commit_generation()
            return

        # Verify all new candidates
        for candidate in new_candidates:
            self.verifier.verify(candidate)
            self._emit_verified(candidate)

        # Reflect on failures
        for candidate in new_candidates:
            if candidate.is_failed:
                if self.model_calls >= self.config.model_call_budget:
                    self.stop_reason = "model_call_budget_exhausted"
                    logger.warning("Model call budget exhausted during reflection")
                    break
                if not self._before_call(gen, "reflect", candidate.id):
                    break
                self._reflect(candidate, gen)

        # Add to population
        for candidate in new_candidates:
            self.population.add(candidate)

        # Cull
        discarded = self.population.cull()
        if discarded:
            logger.info("Discarded %d candidates", len(discarded))
            self.events.emit("candidates_discarded", gen=gen, ids=[c.id for c in discarded])

        # Check stop conditions before committing so the checkpoint
        # captures the updated counter/reason atomically.
        self._check_stop_conditions()

        # Commit (includes stop_reason + consecutive_all_failed)
        self._commit_generation()

        # Dashboard
        if gen % self.config.dashboard_interval == 0:
            self._emit_dashboard()

    def _commit_generation(self) -> None:
        """Commit the current generation state atomically."""
        bound_dict = {
            "n_max": self.config.bound.n_max,
            "n_random": self.config.bound.n_random,
            "seq_len_max": self.config.bound.seq_len_max,
            "seq_count": self.config.bound.seq_count,
            "seed": self.config.bound.seed,
        }
        best = self.population.best_fitness
        self.fitness_history.append(best)
        self.checkpoint.commit(
            generation=self.generation,
            run_id=self.run_id,
            problem=self.config.problem,
            bound=bound_dict,
            candidates=self.population.candidates,
            model_calls=self.model_calls,
            consecutive_all_failed=self.consecutive_all_failed,
            fitness_history=self.fitness_history,
            stop_reason=self.stop_reason,
        )
        top = self.population.best_candidate
        self.events.emit(
            "gen_committed", gen=self.generation,
            population=[{"id": c.id, "parent_ids": c.parent_ids, "state": c.state.value,
                         "fitness": c.fitness, "work_ratio": c.work_ratio}
                        for c in self.population.candidates],
            best_id=top.id if top else None, best_fitness=best,
            best_work_ratio=top.work_ratio if top else None,
            model_calls=self.model_calls, stop_reason=self.stop_reason,
        )
        logger.info("Generation %d committed: best_fitness=%.2f, pop_size=%d",
                     self.generation, best, self.population.size)

    def _check_stop_conditions(self) -> None:
        """Check all stop conditions and set stop_reason if met."""
        if self.stop_reason:
            return

        # Stop on success: any candidate reaches fitness 1.0
        if self.config.early_stop_on_success and self.population.has_passing:
            self.stop_reason = "success"
            logger.info("SUCCESS: candidate reached fitness 1.0 at generation %d", self.generation)
            return

        # Stop on max generations
        if self.generation >= self.config.max_generations:
            self.stop_reason = "max_generations"
            logger.info("Max generations reached (%d)", self.config.max_generations)
            return

        # Stop on consecutive all-failed generations
        all_failed = all(c.is_failed for c in self.population.candidates) if self.population.candidates else True
        if all_failed:
            self.consecutive_all_failed += 1
            if self.consecutive_all_failed >= self.config.max_consecutive_all_failed:
                self.stop_reason = "consecutive_all_failed"
                logger.warning("Stopping: %d consecutive all-failed generations",
                              self.consecutive_all_failed)
        else:
            self.consecutive_all_failed = 0

        # Stop on model call budget
        if self.model_calls >= self.config.model_call_budget:
            self.stop_reason = "model_call_budget_exhausted"
            logger.warning("Model call budget exhausted (%d)", self.model_calls)

    def _emit_dashboard(self) -> None:
        """Emit a dashboard HTML snapshot."""
        generations_data = []
        for gen_num in range(1, self.generation + 1):
            gen_data = self.checkpoint.load_generation(gen_num)
            if gen_data:
                generations_data.append(gen_data)

        self.dashboard.render(
            generation=self.generation,
            config=self.config.to_dict(),
            generations_data=generations_data,
            run_id=self.run_id,
        )

    def _export_summary(self) -> dict[str, Any]:
        """Export final run summary."""
        best = self.population.best_candidate

        # Emit final dashboard
        self._emit_dashboard()

        summary = {
            "run_id": self.run_id,
            "problem": self.config.problem,
            "generation": self.generation,
            "stop_reason": self.stop_reason,
            "best_fitness": best.fitness if best else 0.0,
            "best_candidate_id": best.id if best else None,
            "best_work_ratio": best.work_ratio if best else None,
            "total_candidates": len(self.population.candidates),
            "passing_candidates": sum(1 for c in self.population.candidates if c.is_passing),
            "model_calls": self.model_calls,
            "fitness_history": self.fitness_history,
            "config": self.config.to_dict(),
        }

        # Write summary
        results_dir = self.run_dir / "results"
        results_dir.mkdir(exist_ok=True)
        import json
        (results_dir / "run_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False)
        )

        # Efficiency report CSV
        csv_lines = ["candidate_id,generation,fitness,work_ratio,state,timeout,tests_passed,tests_total"]
        for gen_num in range(1, self.generation + 1):
            gen_data = self.checkpoint.load_generation(gen_num)
            if gen_data:
                for c in gen_data.get("candidates", []):
                    csv_lines.append(
                        f"{c['id']},{gen_num},{c.get('fitness', 0)},"
                        f"{c.get('work_ratio', '')},{c['state']},"
                        f"{c.get('timeout', False)},{c.get('tests_passed', 0)},"
                        f"{c.get('tests_total', 0)}"
                    )
        (results_dir / "efficiency_report.csv").write_text("\n".join(csv_lines))

        logger.info("Run %s complete: %s (best_fitness=%.2f, %d generations)",
                     self.run_id, self.stop_reason,
                     summary["best_fitness"], self.generation)

        return summary

    def status(self) -> dict[str, Any]:
        """Return current run status for CLI."""
        return {
            "run_id": self.run_id,
            "generation": self.generation,
            "best_fitness": self.population.best_fitness,
            "population_size": self.population.size,
            "passing": self.population.has_passing,
            "stop_reason": self.stop_reason,
            "model_calls": self.model_calls,
            "consecutive_all_failed": self.consecutive_all_failed,
        }
