#!/usr/bin/env python3
"""Raw-data landing check (deterministic). data-runner runs it after every batch; the main session may re-run it.

Usage:
  validate_raw.py <topic_dir> [--fix]
  validate_raw.py <topic_dir> --topn --csv <file> --entity-col <col> --dim-col <col> --expect-dims N [--weight-col <col>] [--n 12]

Conventions (data-runner follows them when landing files):
  raw/YYYYMMDD_<content>_<REGION>.csv       pattern comes from adapter.json raw_name_pattern
  raw/<same>.sql                             the executed SQL, header block included
  raw/<same>.meta.json                       {"rowCount": engine-side rows, "fetched": rows retrieved, "taskId": "...", "region": "..."}
  LOG.md                                     one line per raw file

Checks: naming / sibling .sql / .meta.json present / fetched == rowCount / LOG.md entry
  --fix   rename truncated sets to _TRUNCATED_DO_NOT_USE_<name>.*
  --topn  the N heaviest entities must be "full" on the dim column (unordered truncation leaves head entities with missing cells)
Exit: 0 / 1
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import harness_config as hc  # noqa: E402


def check_dir(topic, fix, name_rx):
    raw = os.path.join(topic, "raw")
    log_path = os.path.join(topic, "LOG.md")
    log = open(log_path, encoding="utf-8").read() if os.path.exists(log_path) else ""
    errs, oks = [], []
    if not os.path.isdir(raw):
        return [f"missing raw/ directory: {raw}"], []
    for fn in sorted(os.listdir(raw)):
        if not fn.endswith(".csv") or fn.startswith("_TRUNCATED"):
            continue
        base = fn[:-4]
        if not name_rx.match(fn):
            errs.append(f"{fn}: name does not match {name_rx.pattern}")
        if not os.path.exists(os.path.join(raw, base + ".sql")):
            errs.append(f"{fn}: missing sibling .sql")
        meta_p = os.path.join(raw, base + ".meta.json")
        if not os.path.exists(meta_p):
            errs.append(f"{fn}: missing .meta.json (rowCount/fetched/taskId/region) — without it truncation cannot be ruled out")
        else:
            try:
                m = json.load(open(meta_p, encoding="utf-8"))
                rc, fe = m.get("rowCount"), m.get("fetched")
                if rc is None or fe is None:
                    errs.append(f"{fn}: meta lacks rowCount or fetched")
                elif int(rc) != int(fe):
                    errs.append(f"{fn}: TRUNCATED — fetched={fe} != rowCount={rc}")
                    if fix:
                        for ext in (".csv", ".sql", ".meta.json"):
                            src = os.path.join(raw, base + ext)
                            if os.path.exists(src):
                                os.rename(src, os.path.join(raw, "_TRUNCATED_DO_NOT_USE_" + base + ext))
                        errs[-1] += " → renamed and quarantined"
            except Exception as e:  # noqa
                errs.append(f"{fn}: meta unreadable: {e}")
        if base not in log and fn not in log:
            errs.append(f"{fn}: not registered in LOG.md")
        if not any(er.startswith(fn) for er in errs):
            oks.append(fn)
    return errs, oks


def topn(topic, csv_name, entity, dim, expect, weight, n):
    rows = list(csv.DictReader(open(os.path.join(topic, "raw", csv_name), encoding="utf-8-sig")))
    w, dims = defaultdict(float), defaultdict(set)
    for r in rows:
        try:
            w[r[entity]] += float(r[weight]) if weight else 1.0
        except (ValueError, KeyError):
            w[r[entity]] += 1.0
        dims[r[entity]].add(r[dim])
    top = sorted(w, key=w.get, reverse=True)[:n]
    return top, [(e, len(dims[e])) for e in top if len(dims[e]) < expect]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topic_dir")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--topn", action="store_true")
    ap.add_argument("--csv")
    ap.add_argument("--entity-col")
    ap.add_argument("--dim-col")
    ap.add_argument("--expect-dims", type=int)
    ap.add_argument("--weight-col")
    ap.add_argument("--n", type=int, default=12)
    a = ap.parse_args()
    cfg = hc.load()
    name_rx = re.compile(hc.get(cfg, "operations.workspace.raw_name_pattern") or r"^\d{8}_.+_[A-Za-z]+\.csv$")
    rc = 0
    if a.topn:
        if not all([a.csv, a.entity_col, a.dim_col, a.expect_dims]):
            print("ERROR: --topn needs --csv --entity-col --dim-col --expect-dims")
            sys.exit(2)
        top, bad = topn(a.topic_dir, a.csv, a.entity_col, a.dim_col, a.expect_dims, a.weight_col, a.n)
        print(f"== top-{a.n} completeness {a.csv} ({a.entity_col} × {a.dim_col}, expect {a.expect_dims}) ==")
        if bad:
            rc = 1
            for e, k in bad:
                print(f"ERROR: head entity {e} has only {k}/{a.expect_dims} {a.dim_col} values — truncation signal; split the query by dimension and re-run")
        else:
            print(f"OK: top-{len(top)} entities are complete")
    else:
        errs, oks = check_dir(a.topic_dir, a.fix, name_rx)
        print(f"== raw check {a.topic_dir} {hc.describe(cfg)} ==")
        for o in oks:
            print("OK:   ", o)
        for e in errs:
            print("ERROR:", e)
        rc = 1 if errs else 0
    sys.exit(rc)


if __name__ == "__main__":
    main()
