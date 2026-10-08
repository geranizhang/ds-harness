#!/usr/bin/env python3
import argparse, json
from collections import Counter, defaultdict
from pathlib import Path

CASES = Path(__file__).parent / "cases.jsonl"
TWEAK_TOPICS_THRESHOLD = 3

p = argparse.ArgumentParser(description="Review the corrections ledger: counts, violations by rule, generalize candidates, recurring tweaks.")
p.add_argument("--tags", action="store_true")
p.add_argument("--promote", type=int)
p.add_argument("--to")
p.add_argument("--dismiss", type=int)
p.add_argument("--all", action="store_true", help="include promoted / dismissed")
a = p.parse_args()

rows = [json.loads(l) for l in CASES.read_text().splitlines() if l.strip()] if CASES.exists() else []

if a.promote or a.dismiss:
    tid = a.promote or a.dismiss
    for r in rows:
        if r["id"] == tid:
            if a.promote:
                if not a.to:
                    raise SystemExit("--promote needs --to memory:<slug> / skill:<file> / adapter:<file>")
                r["status"], r["promoted_to"] = "promoted", a.to
            else:
                r["status"] = "dismissed"
            break
    else:
        raise SystemExit(f"no case #{tid}")
    CASES.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"#{tid} -> {r['status']}")
    raise SystemExit

if a.tags:
    for tag, n in Counter(r["tag"] for r in rows).most_common():
        print(f"{n:3d}  {tag}")
    raise SystemExit

print(f"{len(rows)} cases: open {sum(r['status']=='open' for r in rows)}, promoted {sum(r['status']=='promoted' for r in rows)}, dismissed {sum(r['status']=='dismissed' for r in rows)}\n")

print("## by kind × stage")
for (k, s), n in sorted(Counter((r["kind"], r["stage"]) for r in rows).items()):
    print(f"  {k:10s} {s:12s} {n}")

print("\n## violations: rule exists but was not followed (by rule; feed graders / regressions)")
by_rule = defaultdict(list)
for r in rows:
    if r["kind"] == "violation":
        by_rule[r["existing_rule"]].append(r)
for rule, rs in sorted(by_rule.items(), key=lambda x: -len(x[1])):
    topics = sorted({f"{r['project']}/{r['topic']}" for r in rs})
    print(f"  {len(rs)}×  {rule}   topics: {', '.join(topics)}")
if not by_rule:
    print("  (none)")

print("\n## generalize: awaiting the user's decision")
pend = [r for r in rows if r["kind"] == "generalize" and r["status"] == "open"]
for r in pend:
    print(f"  #{r['id']} [{r['stage']}] {r['tag']}\n      user: {r['user_words'] or r['user_correction']}")
if not pend:
    print("  (none)")

print(f"\n## tweak: same tag across ≥{TWEAK_TOPICS_THRESHOLD} topics — possibly an unwritten preference")
tw = defaultdict(set)
for r in rows:
    if r["kind"] == "tweak" and r["status"] != "dismissed":
        tw[r["tag"]].add(f"{r['project']}/{r['topic']}")
hits = {t: ts for t, ts in tw.items() if len(ts) >= TWEAK_TOPICS_THRESHOLD}
for t, ts in sorted(hits.items(), key=lambda x: -len(x[1])):
    ids = [str(r["id"]) for r in rows if r["kind"] == "tweak" and r["tag"] == t]
    print(f"  {t}  ×{len(ts)} topics  (#{', #'.join(ids)})")
if not hits:
    single = sum(1 for ts in tw.values() if len(ts) < TWEAK_TOPICS_THRESHOLD)
    print(f"  (none; {single} tags below threshold, leave them)")
