#!/usr/bin/env python3
"""Report draft check (deterministic). report-writer runs it in draft and review; the main session runs it again before publishing.

Usage:
  validate_doc.py <draft.md> --topic-dir <dir> [--vocab <file>] [--report <out.md>] [--numbers-warn]

Checks (all word lists, section names and regexes come from adapter.json "doc"):
  A structure   background + conclusions sections exist (ERROR); forbidden standalone sections (ERROR);
                after conclusions, every perspective section opens with a bold claim (WARN; appendix/case subtrees
                and container sections with ≤2 intro lines are skipped)
  B banned      confidence labels, colloquialisms, known invented terms (ERROR); control/DiD column in body table (WARN)
  C vocabulary  candidate terms not in vocab and not defined in a quote block/table → listed for a human, no failure
  D numbers     every number in body text (not quotes, not tables) must be found in topic_dir deliverables/raw/work
                csv/xlsx or an in-document table (tolerance = half a unit of the shown precision; % also matches 0.xx)
                → ERROR (--numbers-warn downgrades)
  E sentences   comparison word without a comparison anchor ("than / vs / from…to") → WARN
Exit: 0 / 1 (A, B or D errors) / 3 missing dependency
"""
import argparse
import csv
import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import harness_config as hc  # noqa: E402

NUM_RE = None  # built from adapter units


def build_patterns(doc):
    global NUM_RE
    units = doc.get("number_units") or ["%", "pp", "x", "×", "k", "K", "M", "B"]
    NUM_RE = re.compile(r"(?<![\w.])([-+−]?\d[\d,]*(?:\.\d+)?)\s*(" + "|".join(map(re.escape, units)) + r")?(?![\w.])")
    coll = [re.escape(w) for w in doc.get("colloquial_words") or []]
    extra = doc.get("colloquial_extra_regex")
    coll_re = re.compile("|".join(coll + ([extra] if extra else [])), re.I) if (coll or extra) else None
    pats = {
        "colloquial": coll_re,
        "conf": hc.compile_all(doc.get("confidence_label_patterns")),
        "forbidden_sec": hc.compile_all(doc.get("forbidden_sections")),
        "control": hc.compile_all(doc.get("control_column_patterns")),
        "skip": re.compile("|".join(map(re.escape, doc.get("section_skip") or [])), re.I) if doc.get("section_skip") else re.compile(r"$^"),
        "cmp": re.compile("|".join(map(re.escape, doc.get("comparison_words") or [])), re.I) if doc.get("comparison_words") else None,
        "cmp_ok": re.compile("|".join(doc.get("comparison_ok") or [])) if doc.get("comparison_ok") else re.compile(r"$^"),
    }
    sfx = doc.get("term_suffixes") or []
    if doc.get("cjk_suffix_terms"):
        pats["suffix"] = re.compile(r"[一-鿿]{1,6}(" + "|".join(map(re.escape, sfx)) + ")") if sfx else None
    else:
        pats["suffix"] = re.compile(r"\b[A-Za-z][a-z]+(?:[- ][a-z]+){0,2}\s(" + "|".join(map(re.escape, sfx)) + r")\b", re.I) if sfx else None
    pats["ascii"] = re.compile(r"(?<![\w/])[A-Za-z][A-Za-z0-9_]{1,}(?![\w/])")
    pats["cjk"] = bool(doc.get("cjk_suffix_terms"))
    return pats


def parse_sections(lines):
    secs, cur = [], {"level": 0, "title": "(preamble)", "lines": []}
    for ln in lines:
        m = re.match(r"^(#{1,6})\s+(.*)", ln)
        if m:
            secs.append(cur)
            cur = {"level": len(m.group(1)), "title": m.group(2).strip(), "lines": []}
        else:
            cur["lines"].append(ln)
    secs.append(cur)
    return secs


def strip_html_comments(lines):
    out, in_c = [], False
    for ln in lines:
        s = ln
        while True:
            if in_c:
                j = s.find("-->")
                if j < 0:
                    s = ""
                    break
                s, in_c = s[j + 3:], False
            i = s.find("<!--")
            if i < 0:
                break
            j = s.find("-->", i + 4)
            if j < 0:
                s, in_c = s[:i], True
                break
            s = s[:i] + s[j + 3:]
        out.append(s)
    return out


def body_lines(sec):
    out = []
    for ln in sec["lines"]:
        s = ln.strip()
        if not s or s.startswith((">", "|", "$$", "<", "![", "[")):
            continue
        out.append(ln)
    return out


def defined_text(lines):
    return "\n".join(l for l in lines if l.strip().startswith((">", "|", "`")))


def load_vocab(path):
    v = set()
    if path and os.path.exists(path):
        for l in open(path, encoding="utf-8"):
            l = l.strip()
            if l and not l.startswith("#"):
                v.add(l)
    return v


ABBREV_RE = re.compile(r"(?<![\w/])[A-Z][A-Z0-9]{1,6}(?![\w/])")        # UV, GMV, CTR
IDENT_RE = re.compile(r"(?<![\w/])[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+(?![\w/])")  # snake_case identifiers


def extract_terms(text, pats, ascii_ignore):
    """Candidate 'terms of art'. CJK mode: suffix compounds + every ASCII token (CJK prose has no spaces, so any
    ASCII token stands out). Non-CJK mode: suffix phrases, ALL-CAPS abbreviations and snake_case identifiers only —
    sweeping every English word would flag ordinary prose."""
    terms = set()
    if pats.get("suffix"):
        terms |= {m.group(0) for m in pats["suffix"].finditer(text)}
    if pats.get("cjk"):
        terms |= {m.group(0) for m in pats["ascii"].finditer(text) if m.group(0) not in ascii_ignore and not m.group(0).isdigit()}
    else:
        terms |= {m.group(0) for m in ABBREV_RE.finditer(text) if m.group(0) not in ascii_ignore}
        terms |= {m.group(0) for m in IDENT_RE.finditer(text) if m.group(0) not in ascii_ignore}
    return terms


def to_float(numstr, unit, mult):
    n = float(numstr.replace(",", "").replace("−", "-"))
    vals = {n}
    if unit == "%":
        vals.add(n / 100)
    elif unit in mult:
        vals.add(n * float(mult[unit]))
    return vals


def decimals(numstr):
    return len(numstr.split(".")[1]) if "." in numstr else 0


def load_table_values(topic_dir, md_lines, mult):
    vals, files = [], []
    for l in md_lines:
        if l.strip().startswith("|"):
            for cell in l.strip().strip("|").split("|"):
                for m in NUM_RE.finditer(cell):
                    vals.extend(to_float(m.group(1), m.group(2), mult))
    for sub in ("deliverables", "raw", "work"):
        files += glob.glob(os.path.join(topic_dir, sub, "**", "*.csv"), recursive=True)
        files += glob.glob(os.path.join(topic_dir, sub, "**", "*.xlsx"), recursive=True)
    for f in files:
        if os.path.basename(f).startswith("_TRUNCATED"):
            continue
        try:
            if f.endswith(".csv"):
                for row in csv.reader(open(f, encoding="utf-8-sig", errors="ignore")):
                    for cell in row:
                        try:
                            v = float(cell.replace(",", "").replace("%", ""))
                            vals.append(v)
                            if "%" in cell:
                                vals.append(v / 100)
                        except ValueError:
                            pass
            else:
                import openpyxl  # noqa
                for ws in openpyxl.load_workbook(f, data_only=True).worksheets:
                    for row in ws.iter_rows(values_only=True):
                        for c in row:
                            if isinstance(c, (int, float)):
                                vals += [float(c), float(c) / 100, float(c) * 100]
                            elif isinstance(c, str):
                                try:
                                    vals.append(float(c.replace(",", "").replace("%", "")))
                                except ValueError:
                                    pass
        except ImportError:
            print("WARN: openpyxl missing; xlsx files skipped in number check")
        except Exception as e:  # noqa
            print(f"WARN: could not read {f}: {e}")
    return vals, files


def matched(numstr, unit, table_vals, mult):
    cands = {abs(c) for c in to_float(numstr, unit, mult)}
    tol = 0.5 * 10 ** (-decimals(numstr))
    big = max(cands)
    for c in cands:
        ctol = tol / 100 if (unit == "%" and c < big) else tol
        if any(abs(abs(v) - c) <= ctol + 1e-12 for v in table_vals):
            return True
    return False


def known_term(t, vocab, cjk):
    if t in vocab:
        return True
    if cjk and re.match(r"^[一-鿿]+$", t):
        return any(t[k:] in vocab for k in range(len(t) - 3, -1, -1) if len(t) - k >= 3)
    if not cjk and " " in t:
        return any(w in vocab for w in t.split())
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft")
    ap.add_argument("--topic-dir", required=True)
    ap.add_argument("--vocab")
    ap.add_argument("--report")
    ap.add_argument("--numbers-warn", action="store_true")
    a = ap.parse_args()
    cfg = hc.load()
    doc = hc.get(cfg, "delivery.doc", {})
    pats = build_patterns(doc)
    mult = doc.get("unit_multipliers") or {"k": 1e3, "K": 1e3, "M": 1e6, "B": 1e9}
    ascii_ignore = set(doc.get("ascii_ignore") or [])
    vocab_rel = hc.get(cfg, "delivery.vocab")
    vocab_path = a.vocab or (str(hc.path(cfg, vocab_rel)) if vocab_rel else None)

    lines = strip_html_comments(open(a.draft, encoding="utf-8").read().splitlines())
    secs = parse_sections(lines)
    skip_rx = hc.compile_all(doc.get("number_skip_patterns") or [
        r"\d{4}-\d{2}-\d{2}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?",  # dates and datetimes
        r"\b\d{1,2}:\d{2}\b",                                   # clock times
        r"\b\d+-(?:day|hour|minute|min|week|month|year|dim)s?\b",  # hyphenated spans
    ])
    out, errs, warns = [], [], []
    titles = [s["title"] for s in secs]

    # A
    if not any(any(k.lower() in t.lower() for k in doc.get("section_background") or ["Background"]) for t in titles):
        errs.append("A missing Background section")
    concl_keys = [k.lower() for k in doc.get("section_conclusions") or ["Conclusions"]]
    concl_idx = next((i for i, t in enumerate(titles) if any(k in t.lower() for k in concl_keys)), None)
    if concl_idx is None:
        errs.append("A missing Conclusions section")
    in_skip, skip_level = False, 0
    for i, s in enumerate(secs):
        if any(rx.search(s["title"]) for rx in pats["forbidden_sec"]):
            errs.append(f"A standalone section '{s['title']}' is not allowed; alternative explanations belong in Conclusions as ❌ hypotheses")
        if s["level"] and (not in_skip or s["level"] <= skip_level):
            in_skip = bool(pats["skip"].search(s["title"]))
            skip_level = s["level"]
        if in_skip or concl_idx is None or i <= concl_idx:
            continue
        nxt = secs[i + 1] if i + 1 < len(secs) else None
        bl = body_lines(s)
        if nxt and nxt["level"] > s["level"] and len(bl) <= 2:
            continue
        first = bl[0].strip() if bl else ""
        if first and not re.match(r"^(?:[-*]\s+|\d+\.\s+)?\*\*", first):
            warns.append(f"A section '{s['title']}' does not open with a bold claim (title = perspective, bold first line = conclusion): {first[:40]}")

    # B
    for s in secs:
        for ln in s["lines"] + [s["title"]]:
            if any(rx.search(ln) for rx in pats["conf"]):
                errs.append(f"B confidence label in document [{s['title']}]: {ln.strip()[:60]}")
            if pats["colloquial"] and not ln.strip().startswith(">"):
                m = pats["colloquial"].search(ln)
                if m:
                    errs.append(f"B colloquialism '{m.group(0)}' [{s['title']}]: {ln.strip()[:60]}")
            for w in doc.get("invented_words") or []:
                if w in ln:
                    errs.append(f"B known invented term '{w}' [{s['title']}]: {ln.strip()[:60]}")
            if ln.strip().startswith("|") and any(rx.search(ln) for rx in pats["control"]):
                warns.append(f"B control/DiD column in a body table [{s['title']}]; control columns stay out of body tables by default")

    # C
    vocab = load_vocab(vocab_path)
    defined = defined_text(lines)
    body_text = "\n".join(l for s in secs for l in body_lines(s))
    unknown = sorted(t for t in extract_terms(body_text, pats, ascii_ignore) if not known_term(t, vocab, bool(doc.get("cjk_suffix_terms"))) and t not in defined)
    out.append(f"## C terms outside vocabulary ({len(unknown)}; a human decides: defined short name / common word / invented)")
    out += [f"- {t}" for t in unknown] or ["- none"]

    # D
    table_vals, files = load_table_values(a.topic_dir, lines, mult)
    checked, unmatched = 0, []
    if concl_idx is not None:
        for s in secs:
            for ln in body_lines(s):
                scan = ln
                for rx in skip_rx:
                    scan = rx.sub(" ", scan)
                for m in NUM_RE.finditer(scan):
                    numstr, unit = m.group(1), m.group(2)
                    raw = numstr.replace(",", "").replace("−", "-")
                    if re.fullmatch(r"(19|20)\d{2}(\d{4})?", raw) or (unit is None and abs(float(raw)) < 10 and "." not in raw):
                        continue
                    checked += 1
                    if not matched(numstr, unit, table_vals, mult):
                        unmatched.append((s["title"], numstr + (unit or ""), ln.strip()[:70]))
    out.append(f"\n## D number trace: {checked} numbers in body, {len(unmatched)} not found in any table ({len(files)} files + in-doc tables)")
    for t, n, ctx in unmatched:
        out.append(f"- [{t}] {n} ← {ctx}")
        (warns if a.numbers_warn else errs).append(f"D number {n} not in any table [{t}]: {ctx}")

    # E
    if pats["cmp"]:
        for s in secs:
            for ln in body_lines(s):
                if pats["cmp"].search(ln) and not pats["cmp_ok"].search(ln):
                    warns.append(f"E comparison without 'compared to what' [{s['title']}]: {ln.strip()[:60]}")

    report = ["# validate_doc report", f"draft: {a.draft}", hc.describe(cfg),
              f"result: {'FAIL' if errs else 'PASS'} (ERROR {len(errs)} / WARN {len(warns)})", "", "## ERROR"]
    report += [f"- {e}" for e in errs] or ["- none"]
    report += ["", "## WARN"] + ([f"- {w}" for w in warns] or ["- none"]) + [""] + out
    text = "\n".join(report)
    print(text)
    if a.report:
        open(a.report, "w", encoding="utf-8").write(text)
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
