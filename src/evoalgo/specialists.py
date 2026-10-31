# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Dynamic agent generation: spawn a specialist agent when the search plateaus.

A plateau is declared at a generation boundary when, over the last
``plateau_window`` generations, the population best improved neither its
fitness by ``plateau_epsilon`` nor its work ratio by ``plateau_epsilon``
(relative). Correctness plateaus and efficiency plateaus both count: on
the calibration problems fitness reaches 1.0 within a few generations, so
in practice the search stalls on cost, not on correctness.

On a plateau a specialist is spawned. It is the generator role with an
extra focus section in its task, written from the dominant signature of
the window: the update kind most failures hit (correctness), or the best
candidate's work ratio (efficiency). Each generation it derives one extra
candidate from the population best. At most ``agent_budget`` specialists
are active at once; one is retired after ``specialist_generations``
generations, or after ``plateau_window`` generations without producing a
new population best.

All state is derived from the run's event log (``agent_spawned``,
``agent_retired``, specialist ``candidate_generated``, ``gen_committed``),
so a resumed run continues with the same specialists.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Specialist:
    name: str
    focus: str
    spawned_gen: int
    produced: list[str] = field(default_factory=list)
    last_gain_gen: int | None = None
    retired: bool = False


def best_history(events: list[dict[str, Any]]) -> list[tuple[int, float, float | None, str | None]]:
    """(gen, best fitness, best work ratio, best id) per committed generation."""
    by_gen: dict[int, tuple[int, float, float | None, str | None]] = {}
    for e in events:
        if e.get("type") == "gen_committed":
            by_gen[e["gen"]] = (e["gen"], e.get("best_fitness") or 0.0,
                                e.get("best_work_ratio"), e.get("best_id"))
    return [by_gen[g] for g in sorted(by_gen)]


def plateaued(history: list[tuple], window: int, epsilon: float) -> bool:
    """True if neither fitness nor work ratio improved over the last ``window`` generations."""
    if window < 1 or len(history) <= window:
        return False
    _, f_old, w_old, _ = history[-1 - window]
    _, f_new, w_new, _ = history[-1]
    if f_new - f_old >= epsilon:
        return False
    if w_old and w_new is not None and (w_old - w_new) / w_old >= epsilon:
        return False
    return True


def specialists(events: list[dict[str, Any]]) -> list[Specialist]:
    """Replay the event log into the list of specialists (active and retired)."""
    pool: dict[str, Specialist] = {}
    owner: dict[str, Specialist] = {}
    prev_best: str | None = None
    for e in events:
        kind = e.get("type")
        if kind == "agent_spawned":
            pool[e["agent"]] = Specialist(e["agent"], e["focus"], e["gen"])
        elif kind == "agent_retired" and e.get("agent") in pool:
            pool[e["agent"]].retired = True
        elif kind == "candidate_generated" and e.get("role") == "specialist" and e.get("agent") in pool:
            # A generation that crashed before its checkpoint is redone with
            # the same candidate ids on resume: count each id once.
            if e["id"] not in pool[e["agent"]].produced:
                pool[e["agent"]].produced.append(e["id"])
            owner[e["id"]] = pool[e["agent"]]
        elif kind == "gen_committed":
            best = e.get("best_id")
            if best != prev_best and best in owner:
                owner[best].last_gain_gen = e["gen"]
            prev_best = best
    return list(pool.values())


def signature(events: list[dict[str, Any]], since_gen: int,
              history: list[tuple]) -> tuple[str, str]:
    """(kind, description) of what the window kept running into."""
    _, best_fitness, best_wr, best_id = history[-1]
    failures = [e for e in events if e.get("type") == "candidate_verified"
                and e.get("gen", 0) >= since_gen and e.get("state") != "PASS"]
    if best_fitness < 1.0 and not failures:
        return "correctness", (f"the best candidate {best_id} reaches fitness {best_fitness:.3f} "
                               "and no recent candidate has done better")
    if best_fitness < 1.0:
        ops = Counter(_op_kind(e.get("failing_case")) for e in failures)
        op, count = ops.most_common(1)[0]
        example = next((e["failing_case"] for e in failures
                        if _op_kind(e.get("failing_case")) == op), None) or {}
        detail = ", ".join(f"{k}: {str(example[k])[:160]}" for k in ("operation", "graph_n", "violation")
                           if k in example)
        return "correctness", (f"{count} of {len(failures)} failing candidates in the last "
                               f"generations fail on '{op}' (example: {detail or 'n/a'})")
    wr = f"{best_wr:.3f}" if best_wr is not None else "unknown"
    return "efficiency", (f"the best candidate {best_id} is correct on the search grade with "
                          f"work ratio {wr}, and no candidate has lowered it recently")


FOCUS_TEMPLATES = {
    "correctness": (
        "You are a specialist agent, added because the search stopped improving. "
        "Signature of the plateau: {sig}. Concentrate only on that case: work out which "
        "invariant clause breaks and why, and fix it in the parent without changing how "
        "other updates are handled."),
    "efficiency": (
        "You are a specialist agent, added because the search stopped getting cheaper. "
        "Signature of the plateau: {sig}. Lower is better; 1.0 is the cost of the offline "
        "recomputation. Find the update cases where the parent still recomputes or scans "
        "more than it needs to, and handle them locally. Keep it correct: a change that "
        "breaks correctness is worse than no change."),
}


def _op_kind(failing_case: dict[str, Any] | None) -> str:
    op = str((failing_case or {}).get("operation") or "unknown")
    return op.split()[0] if op.split() else "unknown"


def boundary_actions(events: list[dict[str, Any]], gen: int, config: Any) -> list[tuple[str, dict]]:
    """Retire and spawn decisions at the boundary after generation ``gen``,
    as (event type, fields) pairs for the orchestrator to emit in order."""
    window, budget = config.plateau_window, config.specialist_generations
    pool = specialists(events)
    actions: list[tuple[str, dict]] = []
    for s in pool:
        if s.retired:
            continue
        if len(s.produced) >= budget:
            reason = "generation_budget"
        elif gen - (s.last_gain_gen or s.spawned_gen) >= window:
            reason = "no_gain"
        else:
            continue
        s.retired = True
        actions.append(("agent_retired", {"gen": gen, "agent": s.name, "reason": reason,
                                          "candidates": len(s.produced),
                                          "gained": s.last_gain_gen is not None}))
    active = [s for s in pool if not s.retired]
    last_spawn = max((s.spawned_gen for s in pool), default=0)
    history = best_history(events)
    if (len(active) < config.agent_budget and gen - last_spawn >= window
            and plateaued(history, window, config.plateau_epsilon)):
        kind, sig = signature(events, gen - window, history)
        name = f"specialist-{len(pool) + 1}"
        _, f, w, best = history[-1]
        actions.append(("plateau_detected", {"gen": gen, "window": window, "kind": kind,
                                             "signature": sig, "best_id": best,
                                             "best_fitness": f, "best_work_ratio": w}))
        actions.append(("agent_spawned", {"gen": gen, "agent": name, "kind": kind, "signature": sig,
                                          "focus": FOCUS_TEMPLATES[kind].format(sig=sig),
                                          "generations": budget}))
    return actions
