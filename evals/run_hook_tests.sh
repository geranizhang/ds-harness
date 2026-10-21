#!/bin/bash
# Hook regression: feed PreToolUse stdin JSON to hooks/guard.sh and check exit codes.
# Test commands come from the adapter's adapter.json "guard.tests" so the same script runs against any adapter:
#   cli            the CLI name as it appears on a command line
#   query_cmd      a normal query command with {sql} placeholder
#   readonly_cmd   a read-only command that must always pass
#   submit_file_cmd (optional) a compliance-region submission with {file}; enables the submit tests
#   submit_id_cmd   (optional) a submission by id with no file; must pass
#   bad_sql / good_sql (optional) SQL bodies (header is prepended) for the submit tests
HERE=$(cd "$(dirname "$0")" && pwd); H="$HERE/../hooks/guard.sh"
export CLAUDE_PLUGIN_ROOT="$HERE/.."
# resolve the adapter exactly as guard.sh and the scripts do (env vars, then the host pointer files, then the template)
A=$(python3 -c "import sys; sys.path.insert(0, '$HERE/../skills/_shared'); import harness_config as hc; print(hc.adapter_dir())")
[ -f "$A/adapter.json" ] || { echo "no adapter.json at $A"; exit 2; }
j() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); v=d
for k in sys.argv[2].split("."): v=(v or {}).get(k)
print("" if v is None else (" ".join(v) if isinstance(v,list) else v))' "$A/adapter.json" "$1"; }
G=compliance.guard.tests
HDR=$(j platform.sql.header_markers); CLI=$(j $G.cli); QCMD=$(j $G.query_cmd); RO=$(j $G.readonly_cmd)
SUBF=$(j $G.submit_file_cmd); SUBID=$(j $G.submit_id_cmd); BAD=$(j $G.bad_sql); GOOD=$(j $G.good_sql)
# approvals dir as the guard sees it (adapter ⊕ profile)
APPR=$(DS_HARNESS_ADAPTER_DIR="$A" python3 -c "import sys, os; sys.path.insert(0, '$HERE/../skills/_shared'); import harness_config as hc; print(os.path.expanduser(hc.get(hc.load(), 'operations.governance.approvals_dir') or '~/.claude/approvals'))")
TOOL=$(j $G.mcp_tool); TOOL=${TOOL:-Bash}
[ -n "$CLI" ] && [ -n "$QCMD" ] || { echo "adapter.json compliance.guard.tests needs at least cli and query_cmd"; exit 2; }
T=$(mktemp -d); rm -rf "$APPR"; pass=0; fail=0
t() { # want tool command label [grep]
  printf '{"tool_name":"%s","tool_input":{"command":%s}}' "$2" "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$3")" | bash "$H" >"$T/out" 2>&1
  r=$?
  if [ "$r" = "$1" ] && { [ -z "$5" ] || grep -q -- "$5" "$T/out"; }; then echo "PASS ($r) $4"; pass=$((pass+1)); else echo "FAIL (got $r want $1) $4"; head -3 "$T/out"; fail=$((fail+1)); fi
}
echo "adapter: $(j name)"
SAMPLE_SQL='SELECT 1 FROM t WHERE pmod(hash(u),1000)=0'
t 2 "$TOOL" "${QCMD//\{sql\}/$SAMPLE_SQL}"                    "sampling blocked"
t 0 "$TOOL" "${QCMD//\{sql\}/SELECT 1 FROM t}"                "normal query allowed"
[ -n "$RO" ] && t 0 "$TOOL" "$RO"                            "read-only allowed"
t 0 Bash "printf '$CLI $SAMPLE_SQL' >> notes.md"             "Bash: keyword inside single quotes ignored"
t 0 Bash "echo \"$CLI pmod(hash(x),10)=0\" > n.md"           "Bash: keyword inside double quotes ignored"
t 0 Bash "cat <<'EOF' > n.md
$CLI query --sql pmod(hash(x),10)=0
EOF"                                                         "Bash: keyword inside heredoc ignored"
t 0 Bash "ls -la"                                            "Bash: unrelated command allowed"
if [ -n "$SUBF" ]; then
  printf -- '-- %s\n%s\n' "$HDR" "$BAD"  > "$T/bad.sql"
  printf -- '-- %s\n%s\n' "$HDR" "$GOOD" > "$T/good.sql"
  t 2 "$TOOL" "${SUBF//\{file\}/$T/bad.sql}"   "compliance submit: bad SQL blocked"  "validate_sql"
  t 0 "$TOOL" "${SUBF//\{file\}/$T/good.sql}"  "compliance submit: good SQL allowed"
  t 2 "$TOOL" "${SUBF//\{file\}/$T/nope.sql}"  "compliance submit: missing file blocked"
  [ -n "$SUBID" ] && t 0 "$TOOL" "$SUBID"      "compliance submit by id allowed"
  t 2 Bash "node /x/$CLI.js ${SUBF//\{file\}/$T/bad.sql}" "Bash direct call: bad SQL blocked" "validate_sql"
fi
mkdir -p "$APPR" && touch "$APPR/sampling"
t 0 "$TOOL" "${QCMD//\{sql\}/$SAMPLE_SQL}"                    "sampling allowed after approval"
rm -rf "$APPR" "$T"
echo "hook: $pass passed, $fail failed"
[ "$fail" = 0 ]
