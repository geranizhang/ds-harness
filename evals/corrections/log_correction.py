#!/usr/bin/env python3
import argparse, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

CASES = Path(__file__).parent / "cases.jsonl"
STAGES = ["gate1", "gate2", "data-runner", "analysis", "adversarial", "gate3", "doc-draft", "gate4", "publish", "followup"]
KINDS = ["explore", "tweak", "violation", "generalize"]
GENERALIZE_WORDS = re.compile(r"以后|默认|所有|一律|不要再|都要|都不|每次|任何时候|always|never|by default|from now on|every time|going forward", re.I)

p = argparse.ArgumentParser(description="Append one correction case to cases.jsonl (see README for kind criteria).")
p.add_argument("--project", required=True)
p.add_argument("--topic", required=True)
p.add_argument("--stage", required=True, choices=STAGES)
p.add_argument("--kind", required=True, choices=KINDS)
p.add_argument("--tag", required=True)
p.add_argument("--agent-output", required=True)
p.add_argument("--user-correction", required=True)
p.add_argument("--user-words", default="")
p.add_argument("--existing-rule", default=None)
a = p.parse_args()

if a.kind == "explore":
    sys.exit("explore is not logged: iterating on the analysis direction is not an agent error.")
if a.kind == "violation" and not a.existing_rule:
    sys.exit("violation requires --existing-rule (memory:<slug> / skill:<file>#<section> / agent:<name>#<rule> / adapter:<file>); if you cannot name it, log tweak.")
if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.tag):
    sys.exit("tag must be lowercase-hyphenated, e.g. region-label-in-chart")
for k in ("agent_output", "user_correction"):
    if len(getattr(a, k)) > 200:
        sys.exit(f"{k} exceeds 200 characters; excerpt, do not paraphrase.")

has_gen = bool(GENERALIZE_WORDS.search(a.user_words))
if a.kind == "generalize" and a.user_words and not has_gen:
    print("note: no generalizing language in user_words; confirm the user is setting a rule, else log tweak.", file=sys.stderr)
if a.kind == "tweak" and has_gen:
    print("note: user_words contain generalizing language; consider logging generalize.", file=sys.stderr)

rows = [json.loads(l) for l in CASES.read_text().splitlines() if l.strip()] if CASES.exists() else []
rec = {
    "id": max((r["id"] for r in rows), default=0) + 1,
    "ts": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H:%M%z"),
    "project": a.project, "topic": a.topic, "stage": a.stage, "kind": a.kind, "tag": a.tag,
    "agent_output": a.agent_output, "user_correction": a.user_correction, "user_words": a.user_words,
    "existing_rule": a.existing_rule, "rule_candidate": a.kind == "generalize",
    "status": "open", "promoted_to": None,
}
with CASES.open("a") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"#{rec['id']} {rec['kind']} {rec['stage']} {rec['tag']}")
