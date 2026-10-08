#!/usr/bin/env python3
"""Pre-submission SQL check (deterministic; replaces "please remember to").

Usage:
  validate_sql.py <file.sql> [...] --region <REGION> [--allow-sampling] [--allow-binning]

Exit: 0 pass (warnings allowed) / 1 errors

Core checks (adapter-independent):
  header   the first N lines carry every header marker (goal / metric definition / scope)
  sampling pmod(hash / TABLESAMPLE / rand()<  → full data by default; --allow-sampling after user approval
  binning  CASE WHEN range→label, NTILE, percentiles, ORDER BY…LIMIT, ratio in SQL → WARN
           (fetch grain ≠ display grain: bin, rank and divide locally so cuts can change without re-running)
Adapter checks: adapters/<name>/checks.py :: sql_checks(sql, region) — dialect and compliance rules.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import harness_config as hc  # noqa: E402

BINNING = [
    (re.compile(r"CASE\s+WHEN[^;]*?(BETWEEN|[<>]=?)[^;]*?THEN\s+'[^']+'", re.I | re.S),
     "CASE WHEN numeric range → string label: the binning is frozen in SQL; output raw values and bin locally"),
    (re.compile(r"\bNTILE\s*\(", re.I), "NTILE in SQL; output raw values and bucket locally"),
    (re.compile(r"(APPROX_)?PERCENTILE(_APPROX)?\s*\(|\bMEDIAN\s*\(", re.I),
     "percentile computed in SQL cannot be re-sliced locally; pull entity-level values if possible, else mark not_resliceable in meta.json"),
    (re.compile(r"ORDER\s+BY[^;]*?\bLIMIT\s+\d+", re.I | re.S),
     "ORDER BY … LIMIT does top-N: the dropped tail is gone; confirm this is a fetch-cap guard, not a display filter"),
    (re.compile(r"/\s*(NULLIF\s*\()?\s*SUM\s*\(", re.I), "ratio computed in SQL; output additive numerator and denominator, divide locally"),
]


def check(path, region, cfg, allow_sampling=False, allow_binning=False):
    s = open(path, encoding="utf-8").read()
    errs, warns = [], []
    sq = cfg.get("sql") or {}
    markers = sq.get("header_markers") or []
    head = "\n".join(s.splitlines()[: int(sq.get("header_lines", 40))])
    missing = [k for k in markers if k not in head]
    if missing:
        errs.append(f"header block is missing {'/'.join(missing)} (all of {'/'.join(markers)} must appear in the first {sq.get('header_lines', 40)} lines)")
    if not allow_sampling and any(rx.search(s) for rx in hc.compile_all(sq.get("sampling_patterns"))):
        errs.append("sampling detected (pmod(hash / TABLESAMPLE / rand()<). Default is full data; pass --allow-sampling only after the user approved")
    if not allow_binning:
        for rx, msg in BINNING:
            if rx.search(s):
                warns.append("grain: " + msg)
    mod = hc.load_checks_module(cfg)
    if mod is not None and hasattr(mod, "sql_checks"):
        e2, w2 = mod.sql_checks(s, region)
        errs += list(e2)
        warns += list(w2)
    elif cfg.get("_is_template"):
        warns.append("no adapter dialect checks loaded (DS_HARNESS_ADAPTER unset); platform rules were not checked")
    return errs, warns


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--region", required=True)
    ap.add_argument("--allow-sampling", action="store_true")
    ap.add_argument("--allow-binning", action="store_true", help="the header block already declares why binning/percentile/top-N must happen in SQL")
    a = ap.parse_args()
    cfg = hc.load()
    aliases = (cfg.get("sql") or {}).get("region_aliases") or {}
    region = aliases.get(a.region, aliases.get(a.region.upper(), a.region)).lower()
    rc = 0
    for f in a.files:
        errs, warns = check(f, region, cfg, a.allow_sampling, a.allow_binning)
        print(f"== {f} [{region}] adapter={cfg['name']} ==")
        for e in errs:
            print("ERROR:", e)
        for w in warns:
            print("WARN: ", w)
        if not errs and not warns:
            print("OK")
        rc |= 1 if errs else 0
    sys.exit(rc)


if __name__ == "__main__":
    main()
