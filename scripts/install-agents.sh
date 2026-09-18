#!/usr/bin/env bash
# Keep the thesis role-agent configs in sync between the repo and ~/.enlcode.
#
# The repo (./agents, ./skills) holds the versioned copies; ~/.enlcode is what
# enlcode actually loads (agents are discovered only from ~/.enlcode/agents/,
# skills from ~/.enlcode/skills/ - verified 2026-09-18; project-local
# .enlcode/ and .kiro/ are NOT loaded).
#
# Usage:
#   ./install-agents.sh            copy repo -> global (fresh-clone setup)
#   ./install-agents.sh --from-global   copy global -> repo (persist edits made in ~/.enlcode)
#
# Idempotent. Refuses to overwrite without confirmation unless --yes is given.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_SRC="$REPO_ROOT/agents"
SKILL_SRC="$REPO_ROOT/skills/dynamic-graph-algorithms"
GLOBAL_AGENTS="$HOME/.enlcode/agents"
GLOBAL_SKILLS="$HOME/.enlcode/skills"

declare -a AGENT_NAMES=(algorithm-generator algorithm-repairer algorithm-reflector)
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
  # global -> repo: persist edits made directly in ~/.enlcode
  for name in "${AGENT_NAMES[@]}"; do
    copy_one "$GLOBAL_AGENTS/$name.json" "$AGENT_SRC/$name.json"
  done
  copy_one "$GLOBAL_SKILLS/$SKILL_NAME/$SKILL_MD" "$SKILL_SRC/$SKILL_MD"
else
  # repo -> global: fresh-clone setup
  for name in "${AGENT_NAMES[@]}"; do
    copy_one "$AGENT_SRC/$name.json" "$GLOBAL_AGENTS/$name.json"
  done
  copy_one "$SKILL_SRC/$SKILL_MD" "$GLOBAL_SKILLS/$SKILL_NAME/$SKILL_MD"
fi

echo "done."