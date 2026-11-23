# AI-assisted code: generated and revised with GLM-5.2, Claude Opus 5.5, Qwen3.8-Flash-Next and Qwen3.8-27B
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Run configuration: YAML loading, validation, and defaults.

Config schema (config.yaml):
  problem: dynamic_mcs          # one of: dynamic_bfs, dynamic_dfs, dynamic_mcs,
                                #   dynamic_scc, dynamic_lbfs, reachability
  pack: null                    # optional problem-pack name or path; when set,
                                #   the problem (checker) comes from the pack
                                #   and overrides `problem`
  provider: opencode            # agent backend: api | opencode | mock
  model: null                   # model id (null = provider default)
  api_base_url: null            # api: openrouter | openai | URL
  api_key_env: null             # api: NAME of the env var holding the key
  agent_max_steps: 12           # api: model turns per role call
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
  plateau_epsilon: 0.01         # min fitness gain or relative work-ratio gain to avoid a plateau
  dynamic_agents: false         # spawn a specialist agent on a plateau (see specialists.py)
  agent_budget: 3               # max concurrently active specialists
  specialist_generations: 3     # candidates (one per generation) before a specialist retires
  max_consecutive_all_failed: 5 # stop after this many all-failed generations
  model_call_budget: 500        # max LLM invocations
  workdir: runs                 # run directory root
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
_WARNED: set[tuple[str, ...]] = set()  # once per key set, not per load

try:
    import yaml
except ImportError:
    yaml = None


VALID_PROBLEMS = {
    "dynamic_bfs", "dynamic_dfs", "dynamic_mcs",
    "dynamic_scc", "dynamic_lbfs", "reachability",
}

VALID_PROVIDERS = {"api", "opencode", "mock"}
MAX_GOAL_CHARS = 2000


class ConfigError(ValueError):
    """A config file that cannot be read or parsed."""


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
    # Agent backend: "api" (built-in tool loop over an OpenAI-compatible
    # endpoint), "opencode" (agent harness) or "mock" (scripted, offline).
    provider: str = "opencode"
    model: str | None = None
    # api backend: endpoint alias (openrouter | openai) or URL, the
    # NAME of the environment variable holding the key, optional CA bundle.
    api_base_url: str | None = None
    api_key_env: str | None = None
    api_ca_cert: str | None = None
    agent_max_steps: int = 12          # model turns per role call
    agent_max_seconds: int = 900       # wall clock per role call
    agent_request_timeout: int = 300   # one HTTP request
    agent_temperature: float = 0.2
    agent_max_tokens: int = 8192       # completion tokens per model turn
    # Reasoning ("thinking") per model turn. Off by default: reasoning models
    # on vLLM spend the whole token budget thinking and never call a tool.
    agent_thinking: bool = False
    api_extra_body: dict[str, Any] | None = None  # passed through to the endpoint
    harness_bin: str | None = None     # opencode binary override
    mock_script: list[str] | None = None
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
    # Dynamic agent generation (contribution 3, optional): on a plateau,
    # spawn a specialist generator (evoalgo.specialists).
    dynamic_agents: bool = False
    agent_budget: int = 3
    specialist_generations: int = 3
    max_consecutive_all_failed: int = 5
    model_call_budget: int = 500
    early_stop_on_success: bool = True
    # Reflection role (failure analysis feeding repair). False = ablation.
    reflection: bool = True
    # Seed for parent selection (None = unseeded). Campaign runs set one per seed.
    selection_seed: int | None = None
    # Search grade (every candidate) vs final grade (best candidate, on
    # `bound`). See Orchestrator.__init__.
    search_n_max: int = 4
    search_seq_count: int = 3
    final_grade: bool = True
    final_timeout_seconds: int = 300   # per verifier chunk in the final grade
    # Harness workspaces: graded checks allowed before the final grade
    # (None = no limit). Enforced by `evoalgo check`, not left to the prompt.
    max_checks: int | None = None
    workdir: str = "runs"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunConfig:
        if not isinstance(data, dict):
            raise ConfigError(f"config must be a mapping of keys to values, got {type(data).__name__}")
        data = dict(data)
        bound_data = data.pop("bound", None) or {}
        if not isinstance(bound_data, dict):
            raise ConfigError("config key 'bound' must be a mapping")
        known_bound = {f.name for f in fields(Bound)}
        bound = Bound(**{k: v for k, v in bound_data.items() if k in known_bound})
        known = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in known}
        unknown = sorted(set(data) - known) + [f"bound.{k}" for k in sorted(set(bound_data) - known_bound)]
        if unknown and tuple(unknown) not in _WARNED:  # a typo would otherwise silently use the default
            _WARNED.add(tuple(unknown))
            logger.warning("ignoring unknown config keys: %s", ", ".join(unknown))
        return cls(bound=bound, **filtered)

    def to_dict(self) -> dict[str, Any]:
        d = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "bound"}
        d["bound"] = {f.name: getattr(self.bound, f.name) for f in fields(Bound)}
        return d

    def _type_errors(self) -> list[str]:
        """Numeric and boolean fields must hold a value of their declared type."""
        kinds = {"bool": "true or false", "int": "an integer", "float": "a number"}
        errors = []
        for obj, prefix in ((self, ""), (self.bound, "bound.")):
            for f in fields(obj):
                base = f.type.removesuffix(" | None")
                value = getattr(obj, f.name)
                if base not in kinds or value is None and base != f.type:
                    continue
                ok = isinstance(value, bool) if base == "bool" else (
                    isinstance(value, int if base == "int" else (int, float))
                    and not isinstance(value, bool))
                if not ok:
                    errors.append(f"{prefix}{f.name} must be {kinds[base]}, got {value!r}")
        return errors

    def validate(self) -> list[str]:
        type_errors = self._type_errors()
        if type_errors:  # the range checks below assume the right types
            return type_errors
        errors: list[str] = []
        if self.pack:
            # A problem pack takes over: resolve it and adopt its checker as
            # the problem. Old configs without a pack are unaffected.
            from .packs import PackError, resolve_pack
            try:
                pack = resolve_pack(self.pack)
            except PackError as e:
                errors.append(str(e))
            else:
                self.problem = pack.checker
        if self.problem not in VALID_PROBLEMS:
            errors.append(f"problem must be one of {VALID_PROBLEMS}, got '{self.problem}'")
        if self.provider not in VALID_PROVIDERS:
            errors.append(f"provider must be one of {VALID_PROVIDERS}, got '{self.provider}'")
        if self.research_goal is not None and len(self.research_goal) > MAX_GOAL_CHARS:
            errors.append(f"research_goal must be at most {MAX_GOAL_CHARS} characters")
        if self.provider == "api":
            if not self.api_base_url:
                errors.append("provider 'api' needs api_base_url (openrouter, openai or a URL)")
            if not self.model:
                errors.append("provider 'api' needs a model id")
        if not (2 <= self.search_n_max <= 8):
            errors.append(f"search_n_max must be 2-8, got {self.search_n_max}")
        if self.max_checks is not None and self.max_checks < 1:
            errors.append(f"max_checks must be >= 1, got {self.max_checks}")
        if self.search_seq_count < 0:
            errors.append(f"search_seq_count must be >= 0, got {self.search_seq_count}")
        if not (10 <= self.final_timeout_seconds <= 3600):
            errors.append(f"final_timeout_seconds must be 10-3600, got {self.final_timeout_seconds}")
        if not (1 <= self.agent_max_steps <= 50):
            errors.append(f"agent_max_steps must be 1-50, got {self.agent_max_steps}")
        if not (10 <= self.agent_max_seconds <= 7200):
            errors.append(f"agent_max_seconds must be 10-7200, got {self.agent_max_seconds}")
        if not (0.0 <= self.agent_temperature <= 2.0):
            errors.append(f"agent_temperature must be 0.0-2.0, got {self.agent_temperature}")
        if not (1 <= self.plateau_window <= 100):
            errors.append(f"plateau_window must be 1-100, got {self.plateau_window}")
        if not (0.0 <= self.plateau_epsilon <= 1.0):
            errors.append(f"plateau_epsilon must be 0.0-1.0, got {self.plateau_epsilon}")
        if not (1 <= self.agent_budget <= 10):
            errors.append(f"agent_budget must be 1-10, got {self.agent_budget}")
        if not (1 <= self.specialist_generations <= 50):
            errors.append(f"specialist_generations must be 1-50, got {self.specialist_generations}")
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
        """Load a config file; raises ConfigError with a readable message."""
        path = Path(path)
        try:
            text = path.read_text()
        except OSError as e:
            raise ConfigError(f"cannot read config {path}: {e.strerror or e}") from None
        try:
            if yaml is None:
                import json
                data = json.loads(text)
            else:
                data = yaml.safe_load(text)
        except Exception as e:  # yaml.YAMLError or json.JSONDecodeError
            mark = getattr(e, "problem_mark", None)
            where = f" (line {mark.line + 1}, column {mark.column + 1})" if mark else ""
            reason = getattr(e, "problem", None) or str(e).splitlines()[0]
            raise ConfigError(f"config {path} is not valid YAML: {reason}{where}") from None
        try:
            return cls.from_dict(data)
        except ConfigError as e:
            raise ConfigError(f"config {path}: {e}") from None
