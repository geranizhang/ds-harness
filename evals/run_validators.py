#!/usr/bin/env python3
"""Regression for the validator scripts. Run after changing any validate_*.py, adapter.json or checks.py.

Usage:
  python3 evals/run_validators.py                # against adapters/_template (core checks only)
  DS_HARNESS_ADAPTER_DIR=/path/to/your-adapter python3 evals/run_validators.py   # adds the adapter's evals_cases.py

Every case reproduces a real incident class:
  truncation  silent unordered fetch cap            → validate_raw must FAIL and --fix must quarantine
  topn        head entities missing cells            → validate_raw --topn must FAIL
  sampling    sampling added without approval       → validate_sql FAIL; --allow-sampling PASS
  binning     bins / ratio / top-N frozen in SQL    → validate_sql WARN; --allow-binning silences
  doc         colloquialism + number not in table   → validate_doc FAIL; clean draft PASS
  xlsx        '=' cell / text rate / missing ALL    → validate_xlsx FAIL
  <adapter>   cases from the adapter's evals_cases.py, if present (e.g. compliance SQL that must fail / pass)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V_SQL = ROOT / "skills/analysis-workflow/scripts/validate_sql.py"
V_RAW = ROOT / "skills/analysis-workflow/scripts/validate_raw.py"
V_DOC = ROOT / "skills/report-writing/scripts/validate_doc.py"
V_XLSX = ROOT / "skills/report-writing/scripts/validate_xlsx.py"
sys.path.insert(0, str(ROOT / "skills" / "_shared"))
import harness_config as hc  # noqa: E402

CFG = hc.load()
ADAPTER = CFG["name"]
ADAPTER_DIR = Path(CFG["_dir"])
HDR = " ".join(CFG["sql"]["header_markers"])
REGIONS = CFG["regions"]
R0 = REGIONS[0]
AGG = CFG.get("aggregate_row_label", "ALL")
REGION_COL = (CFG.get("region_column_names") or ["region"])[0]
results = []


def run(args):
    p = subprocess.run([sys.executable] + [str(a) for a in args], capture_output=True, text=True,
                       env={**os.environ, "DS_HARNESS_ADAPTER_DIR": str(ADAPTER_DIR)})
    return p.returncode, p.stdout + p.stderr


def expect(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"\n      {detail[:500]}"))


def w(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(s)


def case_truncation(tmp):
    t = f"{tmp}/topic_trunc"
    w(f"{t}/raw/20260812_pair_hour_{R0}.csv", "entity,hour,count\na,0,100\na,1,90\n")
    w(f"{t}/raw/20260812_pair_hour_{R0}.sql", f"-- {HDR}\nSELECT 1")
    w(f"{t}/raw/20260812_pair_hour_{R0}.meta.json", json.dumps({"rowCount": 42189, "fetched": 33511, "taskId": "t1", "region": R0}))
    w(f"{t}/LOG.md", f"20260812 | H1 | run | 20260812_pair_hour_{R0}.csv\n")
    rc, out = run([V_RAW, t])
    expect("truncation: fetched!=rowCount detected", rc == 1 and "TRUNCATED" in out, out)
    rc, out = run([V_RAW, t, "--fix"])
    expect("truncation: --fix quarantines", os.path.exists(f"{t}/raw/_TRUNCATED_DO_NOT_USE_20260812_pair_hour_{R0}.csv"), out)
    rc, out = run([V_RAW, t])
    expect("truncation: clean after quarantine", rc == 0, out)


def case_topn(tmp):
    t = f"{tmp}/topic_topn"
    rows = "entity,hour,count\n" + "\n".join(f"e{i % 3},{h},{100 - i}" for i in range(9) for h in range(3 if i % 3 else 2))
    w(f"{t}/raw/20260810_entity_hour_{R0}.csv", rows)
    w(f"{t}/raw/20260810_entity_hour_{R0}.sql", f"-- {HDR}")
    w(f"{t}/raw/20260810_entity_hour_{R0}.meta.json", json.dumps({"rowCount": 21, "fetched": 21}))
    w(f"{t}/LOG.md", f"x | 20260810_entity_hour_{R0}.csv")
    rc, out = run([V_RAW, t, "--topn", "--csv", f"20260810_entity_hour_{R0}.csv", "--entity-col", "entity", "--dim-col", "hour", "--expect-dims", "3", "--weight-col", "count", "--n", "3"])
    expect("topn: head entity with missing cells detected", rc == 1 and "has only" in out, out)


def case_sampling(tmp):
    w(f"{tmp}/samp.sql", f"-- {HDR}\nSELECT * FROM t WHERE pmod(hash(user_id), 1000) = 0 AND date='20260812'")
    rc, out = run([V_SQL, f"{tmp}/samp.sql", "--region", R0])
    expect("sampling: blocked", rc == 1 and "sampling" in out, out)
    rc, out = run([V_SQL, f"{tmp}/samp.sql", "--region", R0, "--allow-sampling"])
    expect("sampling: --allow-sampling passes", rc == 0, out)


def case_binning(tmp):
    s = f"""-- {HDR}  grain: entity×date
SELECT entity_id, date,
       CASE WHEN views BETWEEN 1 AND 100 THEN 'P1' WHEN views > 100 THEN 'P2' END AS tier,
       SUM(reports) / NULLIF(SUM(views), 0) AS report_rate
FROM t GROUP BY entity_id, date, tier ORDER BY SUM(views) DESC LIMIT 4500"""
    w(f"{tmp}/bin.sql", s)
    rc, out = run([V_SQL, f"{tmp}/bin.sql", "--region", R0])
    expect("binning: CASE WHEN range→label warns", rc == 0 and "frozen in SQL" in out, out)
    expect("binning: ratio in SQL warns", "divide locally" in out, out)
    expect("binning: top-N warns", "top-N" in out, out)
    rc, out = run([V_SQL, f"{tmp}/bin.sql", "--region", R0, "--allow-binning"])
    expect("binning: --allow-binning silences", "grain:" not in out, out)


def case_doc(tmp):
    t = f"{tmp}/topic_doc"
    doc = CFG["doc"]
    bg, cl = doc["section_background"][0], doc["section_conclusions"][0]
    coll = doc["colloquial_words"][0]
    conf = "（高置信）" if doc.get("cjk_suffix_terms") else "(high-confidence)"
    w(f"{t}/deliverables/report_tables.csv", f"{REGION_COL},rate_a,rate_b,diff\n{R0},0.00047,0.00035,36%\n{AGG},0.00044,0.0004,10%\n")
    w(f"{t}/deliverables/bad.md", f"# {bg}\nIntro.\n# {cl}\n- rate_a is 36% higher than rate_b {conf}\n# Breakdown\nSegment X {coll}, 52% higher.\n")
    w(f"{t}/deliverables/good.md", f"# {bg}\nIntro.\n# {cl}\n- **H1 holds: rate_a exceeds rate_b by 36% in {R0}**\n# Breakdown\n> scope: {R0}, 20260812\n**rate_a exceeds rate_b by 36%, aggregate diff is 10%.**\n| {REGION_COL} | rate_a | rate_b | diff |\n|---|---|---|---|\n| {R0} | 0.047% | 0.035% | 36% |\n")
    rc, out = run([V_DOC, f"{t}/deliverables/bad.md", "--topic-dir", t])
    expect("doc: colloquialism blocked", rc == 1 and "colloquialism" in out, out)
    expect("doc: confidence label blocked", "confidence label" in out, out)
    expect("doc: 52% not in table blocked", "52%" in out and "not found" in out, out)
    expect("doc: non-bold first line warns", "bold claim" in out, out)
    rc, out = run([V_DOC, f"{t}/deliverables/good.md", "--topic-dir", t])
    expect("doc: clean draft passes", rc == 0, out)


def case_xlsx(tmp):
    try:
        import openpyxl
    except ImportError:
        print("SKIP xlsx: openpyxl missing")
        return
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([REGION_COL, "gift rate", "== title =="])
    ws.append([R0, "18.6%", "x"])
    ws.append([REGIONS[1] if len(REGIONS) > 1 else R0, 12.3, "y"])
    p = f"{tmp}/bad.xlsx"
    wb.save(p)
    rc, out = run([V_XLSX, p])
    expect("xlsx: '=' cell blocked", rc == 1 and "starts with '='" in out, out)
    expect("xlsx: text rate blocked", "stored as text" in out, out)
    expect("xlsx: missing aggregate row blocked", f"'{AGG}' aggregate row" in out, out)
    expect("xlsx: missing provenance blocked", "provenance" in out, out)


def adapter_cases():
    """An adapter may ship evals_cases.py with `cases(ctx) -> list[callable(tmp)]`; ctx exposes run / expect / w / HDR / V_SQL."""
    p = ADAPTER_DIR / "evals_cases.py"
    if not p.exists():
        return []
    import importlib.util
    spec = importlib.util.spec_from_file_location("adapter_evals", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    ctx = {"run": run, "expect": expect, "w": w, "HDR": HDR, "V_SQL": V_SQL, "V_RAW": V_RAW, "V_DOC": V_DOC, "V_XLSX": V_XLSX}
    return list(mod.cases(ctx))


def main():
    tmp = tempfile.mkdtemp(prefix="ds-harness-evals-")
    cases = [case_truncation, case_topn, case_sampling, case_binning, case_doc, case_xlsx] + adapter_cases()
    print(f"adapter: {ADAPTER}")
    try:
        for c in cases:
            print(f"\n=== {c.__name__} ===")
            c(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    fails = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(fails)}/{len(results)} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
