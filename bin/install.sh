#!/bin/bash
# ds-harness installer: one entry point, one host binding per directory under hosts/.
#
#   bin/install.sh --host claude-code --adapter /path/to/adapter [--profile ~/.ds-harness/profile.json]
#   bin/install.sh --host codex       --adapter /path/to/adapter
#   bin/install.sh --uninstall [--host <host>]        remove what the manifest for that host lists; pointers kept unless --all
#   bin/install.sh <adapter_dir>                      0.2 form: same as --host claude-code --adapter <adapter_dir>
#
# The host binding (hosts/<host>/install.py) links skills, renders agents, registers the hook and the declared tools, and
# writes ~/.ds-harness/{adapter,host[,profile]}; scripts, hook and agents resolve the adapter from there.
set -e
CORE="$(cd "$(dirname "$0")/.." && pwd)"
HOST=""; ADAPTER=""; PROFILE=""; UNINSTALL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --host) HOST="$2"; shift 2;;
    --adapter) ADAPTER="$2"; shift 2;;
    --profile) PROFILE="$2"; shift 2;;
    --uninstall) UNINSTALL=1; shift;;
    -h|--help) sed -n 2,10p "$0"; exit 0;;
    *) [ -z "$ADAPTER" ] && ADAPTER="$1"; shift;;
  esac
done
PTR="$HOME/.ds-harness"
if [ "$UNINSTALL" = 1 ]; then
  HOST="${HOST:-$(cat "$PTR/host" 2>/dev/null || echo claude-code)}"
  M="$PTR/installed.$HOST"; [ -f "$M" ] || { echo "nothing installed for host $HOST"; exit 0; }
  while read -r p; do
    if [ -L "$p" ]; then rm "$p" && echo "  removed link $p"
    elif [ -f "$p" ] && [ "$HOST" != "claude-code" ]; then rm "$p" && echo "  removed $p"; fi
  done < "$M"
  rm -f "$M"; echo "uninstalled $HOST (hook entries and tool registrations left in place; pointers in $PTR kept)"; exit 0
fi
HOST="${HOST:-claude-code}"
[ -f "$CORE/hosts/$HOST/host.json" ] || { echo "unknown host '$HOST'; available: $(ls "$CORE/hosts" | grep -v '^_' | grep -v '\.py$' | tr '\n' ' ')"; exit 1; }
[ -n "$ADAPTER" ] || { echo "usage: install.sh --host <host> --adapter <adapter_dir>"; exit 1; }
ADAPTER="$(cd "$ADAPTER" && pwd)"
[ -f "$ADAPTER/adapter.json" ] || { echo "no adapter.json in $ADAPTER"; exit 1; }
NAME=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$ADAPTER/adapter.json")
echo "installing ds-harness core + adapter '$NAME' for host '$HOST'"
python3 "$CORE/hosts/$HOST/install.py" "$ADAPTER"
if [ -n "$PROFILE" ]; then echo "$PROFILE" > "$PTR/profile"; echo "  $PTR/profile -> $PROFILE (profile overlay arrives with spec 0.3)"; fi
echo; python3 "$CORE/hosts/verify.py" "$HOST" || true
echo; echo "done. Open a new $HOST session to load the skills and agents."
