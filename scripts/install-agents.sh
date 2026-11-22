#!/usr/bin/env bash
# AI-assisted code: generated and revised with DeepSeek-V4-Flash
# under the author's direction; reviewed and tested by the author
# (see the thesis section "Use of AI tools").
# Install the thesis role agents and their skill for opencode.
#
# The repo (./agents, ./skills) holds the versioned copies; opencode loads
# global agents from ~/.config/opencode/agents/ and skills from
# ~/.config/opencode/skills/ ($XDG_CONFIG_HOME is honoured).
#
# Usage:
#   ./install-agents.sh                 copy repo -> global (fresh-clone setup)
#   ./install-agents.sh --from-global   copy global -> repo (persist edits)
#
# Idempotent. Refuses to overwrite without confirmation unless --yes is given.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_SRC="$REPO_ROOT/agents"
SKILL_SRC="$REPO_ROOT/skills/dynamic-graph-algorithms"
GLOBAL="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
GLOBAL_AGENTS="$GLOBAL/agents"
GLOBAL_SKILLS="$GLOBAL/skills"

declare -a AGENT_NAMES=(algorithm-generator algorithm-repairer algorithm-reflector evoalgo-researcher)
SKILL_NAME="dynamic-graph-algorithms"
SKILL_MD="SKILL.md"

usage() {
  echo "Usage: $0 [--from-global] [--yes]"
  exit 1
}

FROM_GLOBAL=0
YES=0
for arg in "$@"; do
  case "$arg" in
    --from-global) FROM_GLOBAL=1 ;;
    --yes) YES=1 ;;
    *) usage ;;
  esac
done

copy_one() {
  local src="$1" dst="$2"
  if [[ -e "$dst" && "$YES" -eq 0 ]]; then
    read -r -p "Overwrite $dst? [y/N] " ans || ans=""
    [[ "$ans" =~ ^[Yy]$ ]] || { echo "skipped $dst"; return; }
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  echo "installed $dst"
}

if [[ "$FROM_GLOBAL" -eq 1 ]]; then
  for name in "${AGENT_NAMES[@]}"; do
    copy_one "$GLOBAL_AGENTS/$name.md" "$AGENT_SRC/$name.md"
  done
  copy_one "$GLOBAL_SKILLS/$SKILL_NAME/$SKILL_MD" "$SKILL_SRC/$SKILL_MD"
else
  for name in "${AGENT_NAMES[@]}"; do
    copy_one "$AGENT_SRC/$name.md" "$GLOBAL_AGENTS/$name.md"
  done
  copy_one "$SKILL_SRC/$SKILL_MD" "$GLOBAL_SKILLS/$SKILL_NAME/$SKILL_MD"
fi

echo "done."
