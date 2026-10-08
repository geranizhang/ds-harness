#!/bin/bash
# ds-harness PreToolUse guard. Enforces two things in the environment so they do not depend on the model remembering:
#   1) a compliance-region submission that carries a query file is validated on the spot (validate_sql --region <submit_region>); errors block
#   2) sampling SQL is blocked unless an approval file exists (touched by the main session after the user approved; expires)
# What counts as "the data CLI", what a submission looks like and which region is compliance-bound come from adapters/<name>/adapter.json "guard".
# Exit 2 = block and hand stderr to the model; 0 = allow.

IN=$(cat)
TOOL=$(printf '%s' "$IN" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("tool_name",""))' 2>/dev/null)
CMD=$(printf '%s' "$IN" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("command",""))' 2>/dev/null)
[ -z "$CMD" ] && exit 0

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ADIR="${DS_HARNESS_ADAPTER_DIR:-$ROOT/adapters/${DS_HARNESS_ADAPTER:-_template}}"
CFG="$ADIR/adapter.json"
[ -f "$CFG" ] || exit 0   # no adapter → nothing platform-specific to enforce

read_cfg() { python3 -c 'import sys,json; d=json.load(open(sys.argv[1])); g=d.get("guard",{}); v=g.get(sys.argv[2]); print("|".join(v) if isinstance(v,list) else ("" if v is None else v))' "$CFG" "$1" 2>/dev/null; }
CMD_PAT=$(read_cfg command_patterns)
SUBMIT_PAT=$(read_cfg submit_patterns)
SUBMIT_REGION=$(read_cfg submit_region)
QF_FLAGS=$(read_cfg query_file_flags); QF_FLAGS=${QF_FLAGS:---query-file|--file}
APPR=$(read_cfg approvals_dir); APPR=${APPR:-~/.claude/approvals}; APPR="${APPR/#\~/$HOME}"
TTL=$(read_cfg approval_ttl_seconds); TTL=${TTL:-86400}
SAMPLING_PAT=$(python3 -c 'import sys,json; d=json.load(open(sys.argv[1])); print("|".join(d.get("sql",{}).get("sampling_patterns",[])))' "$CFG" 2>/dev/null)

# Bash: look only at the command skeleton (strip quoted strings and heredocs) so mentioning a keyword in text does not trigger
STRIPPED="$CMD"
if [ "$TOOL" = "Bash" ]; then
  STRIPPED=$(printf '%s' "$CMD" | python3 -c '
import sys,re
s=sys.stdin.read()
s=re.sub(r"<<-?\s*[\x27\"]?(\w+)[\x27\"]?[^\n]*\n.*?\n\1\s*$", " ", s, flags=re.S|re.M)
s=re.sub(r"\x27[^\x27]*\x27", " ", s)
s=re.sub(r"\"(?:\\\\.|[^\"\\\\])*\"", " ", s)
print(s)' 2>/dev/null)
  [ -n "$CMD_PAT" ] || exit 0
  printf '%s' "$STRIPPED" | grep -qiE "(^|[;&|(]|\s)($CMD_PAT)(\s|$)" || exit 0
fi

VS="$ROOT/skills/analysis-workflow/scripts/validate_sql.py"
fresh() { [ -f "$1" ] && [ $(( $(date +%s) - $(stat -f %m "$1" 2>/dev/null || stat -c %Y "$1") )) -lt "$TTL" ]; }
first_file() { printf '%s' "$CMD" | grep -oE -- "($QF_FLAGS)[ =]+[^ ]+" | sed -E "s/^($QF_FLAGS)[ =]+//; s/^[\"']|[\"']\$//g" | head -1; }

# 1) compliance-region submission with a query file → validate on the spot
if [ -n "$SUBMIT_PAT" ] && printf '%s' "$STRIPPED" | grep -qiE "$SUBMIT_PAT"; then
  QF=$(first_file)
  if [ -n "$QF" ]; then
    QF_ABS="${QF/#\~/$HOME}"
    if [ ! -f "$QF_ABS" ]; then
      echo "BLOCKED by hook: query file does not exist: $QF (compliance-region submissions must come from a local SQL file so it can be validated and kept)" >&2; exit 2
    fi
    if [ -f "$VS" ]; then
      OUT=$(python3 "$VS" "$QF_ABS" --region "${SUBMIT_REGION:-default}" 2>&1) || { echo "BLOCKED by hook: query file failed validate_sql for region ${SUBMIT_REGION}. Fix and resubmit:
$OUT" >&2; exit 2; }
    else
      echo "WARN hook: validate_sql.py not found at $VS; submission allowed unchecked" >&2
    fi
  fi
fi

# 2) sampling: inline SQL or the referenced file
if [ -n "$SAMPLING_PAT" ]; then
  SQLTXT="$CMD"
  F=$(first_file)
  if [ -n "$F" ] && [ -f "${F/#\~/$HOME}" ]; then SQLTXT="$SQLTXT
$(cat "${F/#\~/$HOME}")"; fi
  if printf '%s' "$SQLTXT" | grep -qiE "$SAMPLING_PAT"; then
    if ! fresh "$APPR/sampling"; then
      echo "BLOCKED by hook: sampling detected. Default is full data; if the query cannot run, bring the failure to the user. After the user explicitly approves sampling, the main session runs: mkdir -p $APPR && touch $APPR/sampling (valid ${TTL}s), then retry." >&2
      exit 2
    fi
  fi
fi
exit 0
