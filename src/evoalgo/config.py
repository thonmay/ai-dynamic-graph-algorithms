"""Run configuration: YAML loading, validation, and defaults.

Config schema (config.yaml):
  problem: dynamic_mcs          # one of: dynamic_bfs, dynamic_dfs, dynamic_mcs,
                                #   dynamic_scc, dynamic_lbfs, reachability
  pack: null                    # optional problem-pack name or path; when set,
                                #   the problem (checker) comes from the pack
                                #   and overrides `problem`
  provider: enlcode             # LLM provider adapter name
  model: null                   # model id (null = provider default)
  generator_agent: algorithm-generator
  repairer_agent: algorithm-repairer
  reflector_agent: algorithm-reflector
  population_size: 8            # 1-50
  max_generations: 50           # 1-1000
  elitism_k: 2                  # top-k survivors per generation
  crossover_enabled: false
  diversity_threshold: 0.8      # pairwise similarity above this triggers injection
  timeout_seconds: 30           # per-candidate wall-clock (1-300)
  bound:
    n_max: 5                    # max graph size for exhaustive testing
    n_random: 20                # random graphs beyond n_max
    seq_len_max: 20             # max operations per sequence
    seq_count: 10               # operation sequences per base graph
    seed: 1337
  dashboard_interval: 10        # emit HTML every N generations
  plateau_window: 10            # generations for plateau detection
  plateau_epsilon: 0.01         # min fitness improvement to avoid plateau
  max_consecutive_all_failed: 5 # stop after this many all-failed generations
  model_call_budget: 500        # max LLM invocations
  workdir: runs                 # run directory root
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


VALID_PROBLEMS = {
    "dynamic_bfs", "dynamic_dfs", "dynamic_mcs",
    "dynamic_scc", "dynamic_lbfs", "reachability",
}

VALID_PROVIDERS = {"enlcode"}
MAX_GOAL_CHARS = 2000


@dataclass
class Bound:
    n_max: int = 5
    n_random: int = 20
    seq_len_max: int = 20
    seq_count: int = 10
    seed: int = 1337


@dataclass
class RunConfig:
    problem: str = "dynamic_mcs"
    pack: str | None = None
    # What the researcher wants to find out in this run; sent to every agent
    # call together with the pack brief. Live hints are separate.
    research_goal: str | None = None
    provider: str = "enlcode"
    model: str | None = None
    generator_agent: str = "algorithm-generator"
    repairer_agent: str = "algorithm-repairer"
    reflector_agent: str = "algorithm-reflector"
    population_size: int = 8
    max_generations: int = 50
    elitism_k: int = 2
    crossover_enabled: bool = False
    diversity_threshold: float = 0.8
    timeout_seconds: int = 30
    bound: Bound = field(default_factory=Bound)
    dashboard_interval: int = 10
    plateau_window: int = 10
    plateau_epsilon: float = 0.01
    max_consecutive_all_failed: int = 5
    model_call_budget: int = 500
    early_stop_on_success: bool = True
    workdir: str = "runs"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunConfig:
        data = dict(data)
        bound_data = data.pop("bound", {})
        known_bound = {f.name for f in fields(Bound)}
        bound = Bound(**{k: v for k, v in bound_data.items() if k in known_bound})
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(bound=bound, **filtered)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "problem": self.problem,
            "pack": self.pack,
            "research_goal": self.research_goal,
            "provider": self.provider,
            "model": self.model,
            "generator_agent": self.generator_agent,
            "repairer_agent": self.repairer_agent,
            "reflector_agent": self.reflector_agent,
            "population_size": self.population_size,
            "max_generations": self.max_generations,
            "elitism_k": self.elitism_k,
            "crossover_enabled": self.crossover_enabled,
            "diversity_threshold": self.diversity_threshold,
            "timeout_seconds": self.timeout_seconds,
            "bound": {
                "n_max": self.bound.n_max,
                "n_random": self.bound.n_random,
                "seq_len_max": self.bound.seq_len_max,
                "seq_count": self.bound.seq_count,
                "seed": self.bound.seed,
            },
            "dashboard_interval": self.dashboard_interval,
            "plateau_window": self.plateau_window,
            "plateau_epsilon": self.plateau_epsilon,
            "max_consecutive_all_failed": self.max_consecutive_all_failed,
            "model_call_budget": self.model_call_budget,
            "early_stop_on_success": self.early_stop_on_success,
            "workdir": self.workdir,
        }
        return d

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.pack:
            # A problem pack takes over: resolve it and adopt its checker as
            # the problem. Old configs without a pack are unaffected.
            from .packs import PackError, resolve_pack
            try:
                pack = resolve_pack(self.pack)
            except PackError as e:
                errors.append(str(e))
            except NotImplementedError as e:
                errors.append(str(e))
            else:
                self.problem = pack.checker
        if self.problem not in VALID_PROBLEMS:
            errors.append(f"problem must be one of {VALID_PROBLEMS}, got '{self.problem}'")
        if self.provider not in VALID_PROVIDERS:
            errors.append(f"provider must be one of {VALID_PROVIDERS}, got '{self.provider}'")
        if self.research_goal is not None and len(self.research_goal) > MAX_GOAL_CHARS:
            errors.append(f"research_goal must be at most {MAX_GOAL_CHARS} characters")
        if not (1 <= self.population_size <= 50):
            errors.append(f"population_size must be 1-50, got {self.population_size}")
        if not (1 <= self.max_generations <= 1000):
            errors.append(f"max_generations must be 1-1000, got {self.max_generations}")
        if not (1 <= self.timeout_seconds <= 300):
            errors.append(f"timeout_seconds must be 1-300, got {self.timeout_seconds}")
        if self.elitism_k < 0:
            errors.append(f"elitism_k must be >= 0, got {self.elitism_k}")
        if self.elitism_k > self.population_size:
            errors.append(f"elitism_k ({self.elitism_k}) cannot exceed population_size ({self.population_size})")
        if not (2 <= self.bound.n_max <= 8):
            errors.append(f"bound.n_max must be 2-8, got {self.bound.n_max}")
        if self.bound.seq_len_max < 1:
            errors.append(f"bound.seq_len_max must be >= 1, got {self.bound.seq_len_max}")
        if self.bound.seq_count < 1:
            errors.append(f"bound.seq_count must be >= 1, got {self.bound.seq_count}")
        if not (0.0 <= self.diversity_threshold <= 1.0):
            errors.append(f"diversity_threshold must be 0.0-1.0, got {self.diversity_threshold}")
        if self.model_call_budget < 1:
            errors.append(f"model_call_budget must be >= 1, got {self.model_call_budget}")
        if self.max_consecutive_all_failed < 1:
            errors.append(f"max_consecutive_all_failed must be >= 1, got {self.max_consecutive_all_failed}")
        if self.dashboard_interval < 1:
            errors.append(f"dashboard_interval must be >= 1, got {self.dashboard_interval}")
        if self.bound.n_random < 0:
            errors.append(f"bound.n_random must be >= 0, got {self.bound.n_random}")
        return errors

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if yaml is None:
            import json
            path.write_text(json.dumps(self.to_dict(), indent=2))
        else:
            path.write_text(yaml.dump(self.to_dict(), default_flow_style=False))

    @classmethod
    def load(cls, path: Path | str) -> RunConfig:
        path = Path(path)
        text = path.read_text()
        if yaml is None:
            import json
            data = json.loads(text)
        else:
            data = yaml.safe_load(text)
        return cls.from_dict(data)
