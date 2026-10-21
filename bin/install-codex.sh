#!/usr/bin/env bash
# Install ds-harness (core) + one adapter for Codex, side by side with the Claude Code install.
#
#   bin/install-codex.sh <adapter_dir>      link core + adapter skills into ~/.agents/skills, write the adapter pointer,
#                                           generate Codex custom agents, register the PreToolUse guard in ~/.codex/hooks.json
#
# Both hosts point at the SAME adapter directory (~/.codex/ds-harness-adapter and ~/.claude/ds-harness-adapter hold the
# same path), so rules, approvals and write-backs are shared. Nothing team-specific is hard-coded here: adapter skills and
# agents are enumerated from adapter.json → extensions, and the optional entry skill comes from extensions.entry_skill.
set -euo pipefail

CORE="$(cd "$(dirname "$0")/.." && pwd)"
ADAPTER="$(cd "${1:?usage: install-codex.sh <adapter_dir>}" && pwd)"
[ -f "$ADAPTER/adapter.json" ] || { echo "no adapter.json in $ADAPTER" >&2; exit 1; }
AGENTS="$HOME/.agents/skills"
CODEX="$HOME/.codex"
BACKUPS="$HOME/.agents/skill-backups"
mkdir -p "$AGENTS" "$CODEX/agents" "$BACKUPS"

cfg() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."): d = d.get(k, {}) if isinstance(d, dict) else {}
print(d if isinstance(d, str) else "")' "$ADAPTER/adapter.json" "$1"; }

link_skill() { # name source
  local target="$AGENTS/$1"
  if [ -L "$target" ]; then ln -sfn "$2" "$target"
  elif [ -e "$target" ]; then mv "$target" "$BACKUPS/$1-$(date +%Y%m%d-%H%M%S)"; ln -s "$2" "$target"
  else ln -s "$2" "$target"; fi
  echo "skill $1 -> $2"
}

for s in analysis-brief analysis-workflow report-writing; do link_skill "$s" "$CORE/skills/$s"; done
SKILLS_DIR="$ADAPTER/$(cfg extensions.skills)"
for s in "$SKILLS_DIR"/*/; do [ -f "$s/SKILL.md" ] && link_skill "$(basename "$s")" "${s%/}"; done

printf '%s\n' "$ADAPTER" > "$CODEX/ds-harness-adapter"
echo "adapter pointer: $CODEX/ds-harness-adapter -> $ADAPTER"

# Codex custom agents (.toml) from the core agents and the adapter's agents; <harness> is spelled out as an absolute path.
AGENTS_DIR="$ADAPTER/$(cfg extensions.agents)"
python3 - "$CORE" "$AGENTS_DIR" "$CODEX/agents" <<'PY'
import json, pathlib, re, sys
core, adapter_agents, target = map(pathlib.Path, sys.argv[1:])
files = sorted((core / "agents").glob("*.md")) + (sorted(adapter_agents.glob("*.md")) if adapter_agents.is_dir() else [])
for src in files:
    text = src.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        continue
    front, body = parts[1], parts[2]
    fields = dict(m.groups() for m in (re.match(r"^(name|description):\s*(.*)$", l) for l in front.splitlines()) if m)
    body = body.replace("`<harness>` is the plugin root", f"`<harness>` is `{core}`").replace("`<harness>` is this repository's root", f"`<harness>` is `{core}`")
    dest = target / f"{fields.get('name', src.stem)}.toml"
    dest.write_text(f'name = {json.dumps(fields.get("name", src.stem), ensure_ascii=False)}\n'
                    f'description = {json.dumps(fields.get("description", ""), ensure_ascii=False)}\n'
                    f'developer_instructions = {json.dumps(body.strip(), ensure_ascii=False)}\n', encoding="utf-8")
    print(f"agent {dest.stem} -> {dest}")
PY

# PreToolUse guard: same script as the Claude Code install; one entry, replacing any earlier ds-harness entry.
python3 - "$CODEX/hooks.json" "$CORE/hooks/guard.sh" <<'PY'
import json, pathlib, sys
path, guard = map(pathlib.Path, sys.argv[1:])
data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"hooks": {}}
pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
pre[:] = [e for e in pre if "ds-harness" not in json.dumps(e)]
pre.append({"matcher": "Bash|mcp__.*__run_command", "hooks": [{"type": "command", "command": f"bash '{guard}'"}]})
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"hook: {path}")
PY

# Optional entry skill: a one-page router under the team's own name (adapter.json → extensions.entry_skill {name, description, body}).
ENTRY=$(cfg extensions.entry_skill.name)
if [ -n "$ENTRY" ]; then
  mkdir -p "$AGENTS/$ENTRY"
  python3 - "$ADAPTER/adapter.json" "$AGENTS/$ENTRY/SKILL.md" <<'PY'
import json, pathlib, sys
cfg = json.load(open(sys.argv[1]))["extensions"]["entry_skill"]
body = cfg.get("body") or ("Use `analysis-workflow` as the end-to-end process, `analysis-brief` for unfamiliar or complex questions, "
                           "and `report-writing` for report structure. Team rules come from the active adapter at `~/.codex/ds-harness-adapter` through its `adapter.json`.")
pathlib.Path(sys.argv[2]).write_text(f"---\nname: {cfg['name']}\ndescription: {cfg.get('description', '')}\n---\n\n{body}\n", encoding="utf-8")
print(f"entry skill {cfg['name']} -> {sys.argv[2]}")
PY
fi

echo
echo "done. Restart Codex to reload skills and agents; review and trust the updated hook when Codex asks."
