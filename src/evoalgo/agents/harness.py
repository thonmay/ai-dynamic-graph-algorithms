# AI-assisted code: generated and revised with Claude Opus 5.5
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
"""Harness backend: an existing coding agent does the call with its own tools.

The harness is told the same role prompt and task text as the api backend,
plus the output path, and must leave the file on disk. The supported harness
is opencode: ``<bin> run [--agent A] --format json --dir RUN [-m MODEL] TASK``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from ..sandbox import JAIL_ENV
from .base import CallLog, CallResult, Task
from .prompts import system_prompt, task_message

ROLE_AGENT = {"generate": "generator_agent", "repair": "repairer_agent", "reflect": "reflector_agent"}

# Environment a coding-agent harness gets: an allow-list, so the API keys and
# passwords of unrelated tools in the user's shell are not handed to the agent
# (whose tool outputs are recorded) or to the model provider. Each harness
# also gets the variables it needs for its own model access.
BASE_ENV = ("HOME", "USER", "LOGNAME", "PATH", "SHELL", "TERM", "LANG", "TZ", "TMPDIR",
            "LD_LIBRARY_PATH", "NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "SSL_CERT_DIR",
            "REQUESTS_CA_BUNDLE", "http_proxy", "https_proxy", "no_proxy",
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "CURL_CA_BUNDLE", "NODE_OPTIONS",
            "ELAN_HOME", "LEAN_PROJECT", "EVOALGO_SANDBOX")
BASE_ENV_PREFIXES = ("LC_", "XDG_")
# Per harness: (names, prefixes) it needs for its own model access.
HARNESS_ENV = {
    # opencode keeps its provider credentials in its own config directory.
    "opencode": (("OPENCODE_PATH",), ("OPENCODE_",)),
    # agy (Antigravity CLI) uses ~/.gemini/antigravity-cli and Gemini/Google env vars.
    "agy": (("AGY_PATH", "GEMINI_API_KEY", "GOOGLE_API_KEY"),
            ("ANTIGRAVITY_", "AGY_", "GEMINI_")),
}


def harness_env(harness: str, **overrides: str) -> dict[str, str]:
    """The allow-listed environment for ``harness`` plus ``overrides``."""
    names, prefixes = HARNESS_ENV.get(harness, ((), ()))
    keep, prefixes = set(BASE_ENV) | set(names), BASE_ENV_PREFIXES + prefixes
    env = {k: v for k, v in os.environ.items() if k in keep or k.startswith(prefixes)}
    return env | overrides


# -- agent jail ---------------------------------------------------------------
#
# The harness agent has a shell, so a prompt rule is not enough to keep it
# from the verifier. It runs in new user, mount and pid namespaces (network
# kept for its model): the evoalgo package, its source checkout and its
# virtual environment are hidden behind tmpfs, the run directory is replaced
# by an empty work directory, and /proc shows only its own processes (the
# engine's environment holds the API keys). Inside a second user namespace it
# cannot unmount what covers the hidden directories. Only the one output file
# is copied back to the run.

# Directories are opened before they are hidden and bound back through the
# descriptor, so this also works when the run is inside the hidden checkout.
# The jail's own tools run before the agent is confined, and the agent can
# write its home, which is on its PATH and LD_LIBRARY_PATH; so they are found
# on a fixed system PATH with no loader variables (jail_env), and the agent's
# own values are set by env only after the inner unshare has dropped root in
# the namespace, so a library the agent plants cannot undo the mounts.
_AGENT_JAIL = r'''
set -e
uid=$1; gid=$2; run=$3; work=$4; extra=$5; shift 5
u=$EVOALGO_UNSHARE; p=$EVOALGO_AGENT_PATH; l=$EVOALGO_AGENT_LD
unset EVOALGO_UNSHARE EVOALGO_AGENT_PATH EVOALGO_AGENT_LD
exec 3<"$work"
if [ -n "$extra" ]; then exec 4<"$extra"; fi
while [ "$1" != "--" ]; do
  if [ -d "$1" ] && [ ! -L "$1" ]; then mount -t tmpfs -o size=1m,mode=755 none "$1"; fi
  shift
done
shift
# A private /tmp and no /run/user: their sockets (tmux, the session bus that
# systemd-run uses) would run commands outside the jail.
mount -t tmpfs -o size=512m,mode=1777 none /tmp
if [ -d "/run/user/$uid" ]; then mount -t tmpfs -o size=1m,mode=700 none "/run/user/$uid"; fi
mkdir -p "$run"
mount --no-canonicalize --bind /proc/self/fd/3 "$run"
if [ -n "$extra" ]; then
  mkdir -p "$extra"
  mount --no-canonicalize --bind /proc/self/fd/4 "$extra"
fi
exec 3<&- 4<&-
mount -t proc proc /proc
cd "$run"
r=0
if [ -n "$l" ]; then set -- LD_LIBRARY_PATH="$l" "$@"; fi
"$u" -U --map-user="$uid" --map-group="$gid" -- /usr/bin/env PATH="$p" "$@" || r=$?
exit "$r"
'''
SYSTEM_PATH = "/usr/bin:/bin:/usr/sbin:/sbin"
UNSHARE = shutil.which("unshare", path=SYSTEM_PATH)

MAX_OUTPUT_BYTES = 1 << 20  # a candidate or reflection; anything larger is not one


def hidden_from_agents() -> list[str]:
    """Trusted code an agent must not read or change: the evoalgo package (the
    verifier, test-graph data and oracles), the source checkout around it,
    and the virtual environment it is installed in. Never the home directory
    or a parent of it, which holds the harness's own configuration."""
    import evoalgo
    pkg = Path(evoalgo.__file__).resolve().parent
    dirs = {pkg}
    if (pkg.parent.parent / "pyproject.toml").is_file():  # source checkout: <root>/src/evoalgo
        dirs.add(pkg.parent.parent)
    if sys.prefix != sys.base_prefix:  # a venv; never the system prefix (/usr)
        dirs.add(Path(sys.prefix).resolve())
    home = Path.home().resolve()
    return sorted(str(d) for d in dirs if d.is_dir() and d != home and d not in home.parents)


def confined(cmd: list[str], run_dir: Path, work: Path, writable: Path | None = None) -> list[str]:
    """``cmd`` wrapped in the agent jail; inside, ``run_dir`` is ``work``, and
    ``writable`` (the Lean project, for the prover) stays visible. Run it
    with ``jail_env``."""
    return [str(UNSHARE), "-rmpf", "--kill-child", "/bin/sh", "-c", _AGENT_JAIL, "agent-jail",
            str(os.getuid()), str(os.getgid()), str(run_dir), str(work),
            str(writable or ""), *hidden_from_agents(), "--", *cmd]


def jail_env(env: dict[str, str]) -> dict[str, str]:
    """``env`` for a ``confined`` command: the jail is set up on the system
    PATH without LD_LIBRARY_PATH; the agent's own values reach its command."""
    out = {k: v for k, v in env.items() if k not in ("PATH", "LD_LIBRARY_PATH")}
    return out | {"PATH": SYSTEM_PATH, "EVOALGO_UNSHARE": str(UNSHARE),
                  "EVOALGO_AGENT_PATH": env.get("PATH", SYSTEM_PATH),
                  "EVOALGO_AGENT_LD": env.get("LD_LIBRARY_PATH", "")}


def jail_error() -> str | None:
    """Why the agent jail cannot run here, or None (also when it is disabled)."""
    if os.environ.get(JAIL_ENV) == "none":
        return None
    if not (sys.platform.startswith("linux") and UNSHARE):
        return ("the agent jail needs Linux user namespaces (unshare); "
                f"set {JAIL_ENV}=none to run the agent unconfined")
    return None


def _collect(work: Path, task: Task) -> None:
    """Copy the agent's output file from the work directory to the run: a
    regular file of its own only (a symlink or hard link could be any file of
    the user)."""
    src = work / task.output_path.relative_to(task.run_dir)
    if src.is_symlink() or not src.is_file():
        return
    st = src.stat()
    if st.st_nlink > 1 or st.st_size > MAX_OUTPUT_BYTES:
        return
    task.output_path.write_bytes(src.read_bytes())


class HarnessBackend:
    name = "harness"

    def __init__(self, config: Any, run_dir: Path):
        self.config = config
        self.run_dir = Path(run_dir)
        self.log = CallLog(self.run_dir)
        self.timeout = config.agent_max_seconds

    def command(self, task: Task, prompt: str) -> list[str]:  # pragma: no cover - per harness
        raise NotImplementedError

    def parse(self, stdout: str) -> tuple[str | None, dict[str, int]]:
        return (stdout.strip()[-2000:] or None), {}

    def run(self, task: Task) -> CallResult:
        entry = self.log.new(self.name, task, self.config.model)
        task.output_path.parent.mkdir(parents=True, exist_ok=True)
        prompt = (f"{system_prompt(task.role)}\n\n---\n\n{task_message(task, False)}\n"
                  f"Write the file to exactly this path: {task.output_path}\n"
                  "You may not run the project's verifier or tests.")
        cmd = self.command(task, prompt)
        entry["command"] = cmd[:-1] + ["<task>"]
        started = time.monotonic()
        result = CallResult(ok=False)
        jailed = os.environ.get(JAIL_ENV) != "none"
        entry["confined"] = jailed
        work = None
        try:
            if jailed:
                # An empty directory the agent sees at the run's path; its
                # inputs are in the prompt.
                (self.run_dir / ".agent").mkdir(exist_ok=True)
                work = Path(tempfile.mkdtemp(prefix=f"{task.candidate_id}-",
                                             dir=self.run_dir / ".agent"))
                (work / task.output_path.parent.name).mkdir()
            if jailed and not shutil.which(cmd[0]):
                raise FileNotFoundError(cmd[0])
            if error := jail_error():
                raise RuntimeError(error)
            argv, env = cmd, harness_env(self.name)
            if jailed:
                argv, env = confined(cmd, self.run_dir, work), jail_env(env)
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=self.timeout,
                                  cwd=self.run_dir, env=env)
            entry.update(returncode=proc.returncode, stderr=proc.stderr[-4000:])
            result.summary, result.usage = self.parse(proc.stdout)
            if proc.returncode != 0:
                result.error = f"exit {proc.returncode}: {proc.stderr[-500:]}"
            if jailed:
                _collect(work, task)
        except FileNotFoundError:
            result.error = f"harness binary not found: {cmd[0]}"
        except subprocess.TimeoutExpired:
            result.error = f"harness timed out after {self.timeout}s"
        except RuntimeError as e:
            result.error = str(e)
        finally:
            if work is not None:
                shutil.rmtree(work, ignore_errors=True)
        result.ok = task.output_path.is_file()
        entry.update(duration_s=round(time.monotonic() - started, 1), ok=result.ok,
                     error=result.error, summary=result.summary, usage=result.usage)
        self.log.write(entry)
        return result


class OpencodeBackend(HarnessBackend):
    """opencode, driven headlessly; ``harness_bin`` overrides the binary."""

    name = "opencode"

    def __init__(self, config: Any, run_dir: Path):
        super().__init__(config, run_dir)
        self.bin = self.find_bin(config.harness_bin)

    @staticmethod
    def find_bin(override: str | None) -> str:
        return override or os.environ.get("OPENCODE_PATH") or shutil.which("opencode") or "opencode"

    def command(self, task: Task, prompt: str) -> list[str]:
        cmd = [self.bin, "run", "--format", "json", "--dir", str(self.run_dir)]
        agent = getattr(self.config, ROLE_AGENT[task.role], None)
        if agent:
            cmd += ["--agent", agent]
        if self.config.model:
            cmd += ["-m", self.config.model]
        return cmd + [prompt]

    def parse(self, stdout: str) -> tuple[str | None, dict[str, int]]:
        texts, usage = [], {"prompt_tokens": 0, "completion_tokens": 0}
        for line in stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict):
                continue
            part = ev.get("part") or {}
            if ev.get("type") == "text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
            elif ev.get("type") == "step_finish":
                tokens = part.get("tokens") or {}
                usage["prompt_tokens"] += int(tokens.get("input") or 0)
                usage["completion_tokens"] += int(tokens.get("output") or 0)
        return (texts[-1].strip() if texts else None), usage


class AgyBackend(HarnessBackend):
    """Antigravity CLI (``agy``), driven headlessly; ``harness_bin`` overrides the binary."""

    name = "agy"

    def __init__(self, config: Any, run_dir: Path):
        super().__init__(config, run_dir)
        self.bin = self.find_bin(config.harness_bin)

    @staticmethod
    def find_bin(override: str | None) -> str:
        return override or os.environ.get("AGY_PATH") or shutil.which("agy") or "agy"

    def command(self, task: Task, prompt: str) -> list[str]:
        cmd = [
            self.bin, "-p",
            "--output-format", "json",
            "--mode", "auto",
            "--disable-slash-commands",
            "--print-timeout", f"{self.timeout}s",
        ]
        if self.config.model:
            cmd += ["--model", self.config.model]
        # Prompt last so HarnessBackend.run() redacts it with cmd[:-1] + ["<task>"].
        return cmd + [prompt]

    def parse(self, stdout: str) -> tuple[str | None, dict[str, int]]:
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        raw = stdout.strip()
        if not raw:
            return None, usage
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            # Fall back to NDJSON / plain text if stream-json or mixed output was emitted.
            return super().parse(stdout)
        if not isinstance(obj, dict):
            return super().parse(stdout)
        text = obj.get("result") or obj.get("response") or obj.get("text")
        if isinstance(obj.get("usage"), dict):
            u = obj["usage"]
            usage["prompt_tokens"] = int(u.get("input_tokens") or u.get("prompt_tokens") or 0)
            usage["completion_tokens"] = int(u.get("output_tokens") or u.get("completion_tokens") or 0)
        return (text.strip() if isinstance(text, str) and text.strip() else None), usage

