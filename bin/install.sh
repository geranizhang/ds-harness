#!/bin/bash
# Install ds-harness (core) + one adapter into ~/.claude as loose files, so the result behaves as one named workflow.
#
#   bin/install.sh <adapter_dir>            install core skills/agents/hook + the adapter's extensions; record the adapter path
#   bin/install.sh --uninstall              remove what a previous install linked (leaves user content alone)
#
# What it does:
#   ~/.claude/skills/<name>   → symlink to core skills (analysis-brief, analysis-workflow, report-writing, _shared) and adapter skills/*
#   ~/.claude/agents/<name>.md→ symlink to core agents and adapter agents/*.md
#   ~/.claude/hooks/ds-harness-guard.sh → symlink to hooks/guard.sh; a PreToolUse entry is added to ~/.claude/settings.json if absent
#   ~/.claude/ds-harness-adapter          → one line: the adapter path (read by scripts, hook and agents when no env var is set)
# Symlinks mean edits in the repositories are live immediately; nothing is copied.
set -e
CORE="$(cd "$(dirname "$0")/.." && pwd)"
CL="$HOME/.claude"
MANIFEST="$CL/ds-harness.installed"

link() { # src dst
  mkdir -p "$(dirname "$2")"
  if [ -e "$2" ] && [ ! -L "$2" ]; then echo "  skip (exists, not a symlink): $2"; return; fi
  ln -sfn "$1" "$2"; echo "$2" >> "$MANIFEST"; echo "  $2 -> $1"
}

if [ "$1" = "--uninstall" ]; then
  [ -f "$MANIFEST" ] || { echo "nothing installed"; exit 0; }
  while read -r p; do [ -L "$p" ] && rm "$p" && echo "  removed $p"; done < "$MANIFEST"
  rm -f "$MANIFEST" "$CL/ds-harness-adapter"
  echo "uninstalled (settings.json hook entry left in place; remove by hand if desired)"; exit 0
fi

ADAPTER="$(cd "${1:?usage: install.sh <adapter_dir> | --uninstall}" && pwd)"
[ -f "$ADAPTER/adapter.json" ] || { echo "no adapter.json in $ADAPTER"; exit 1; }
NAME=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$ADAPTER/adapter.json")
: > "$MANIFEST"
echo "installing ds-harness core + adapter '$NAME'"

echo "skills:"
for s in analysis-brief analysis-workflow report-writing _shared; do link "$CORE/skills/$s" "$CL/skills/$s"; done
for s in "$ADAPTER"/skills/*/; do [ -d "$s" ] && [ -f "$s/SKILL.md" ] && link "${s%/}" "$CL/skills/$(basename "$s")"; done
echo "agents:"
for a in "$CORE"/agents/*.md; do link "$a" "$CL/agents/$(basename "$a")"; done
for a in "$ADAPTER"/agents/*.md; do [ -f "$a" ] && link "$a" "$CL/agents/$(basename "$a")"; done
echo "hook:"
link "$CORE/hooks/guard.sh" "$CL/hooks/ds-harness-guard.sh"
python3 - "$CL/settings.json" <<'EOF'
import json, sys, os
p = sys.argv[1]
d = json.load(open(p)) if os.path.exists(p) else {}
entry = {"matcher": "Bash|mcp__.*__run_command", "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/ds-harness-guard.sh"}]}
pre = d.setdefault("hooks", {}).setdefault("PreToolUse", [])
if not any("ds-harness-guard" in json.dumps(e) for e in pre):
    pre.append(entry); json.dump(d, open(p, "w"), ensure_ascii=False, indent=2); open(p, "a").write("\n"); print("  settings.json: PreToolUse entry added")
else:
    print("  settings.json: PreToolUse entry present")
EOF
echo "$ADAPTER" > "$CL/ds-harness-adapter"
echo "adapter pointer: $CL/ds-harness-adapter -> $ADAPTER"
echo
echo "done. Open a new Claude Code session to load the skills and agents."
echo "Optional, for shells that run the scripts directly: export DS_HARNESS_ADAPTER_DIR=$ADAPTER"
