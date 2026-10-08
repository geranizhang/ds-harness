---
name: report-writing
description: Structure and writing rules for data-analysis reports — turn analysis results into a report that managers and partner teams understand in one read. Structure follows the team's exemplar reports (background → conclusions → perspectives → appendix); outline before prose; hypotheses enter conclusions as ✅/❌ with explained share; every claim carries numeric bullets and a table; full metric names, complete sentences, complex logic as definition + visual + one plain-language sentence; no invented or colloquial terms; table and file formats. Use when the user wants an analysis written up or published, wants a report outline, is writing or revising conclusions, or polishing report prose.
---

# Report writing

Covers **how the report is presented**: how sections are ordered, how claims and evidence sit together, how sentences are written, what format tables and files take. Neighbours: `analysis-brief` produces the hypothesis tree beforehand; `analysis-workflow` runs the analysis and dispatches; the `report-writer` agent drafts by these rules and runs the validators; the main session publishes by these rules.

**Structure follows `references/structure.md`** (the skeleton distilled from exemplar reports) and the matching exemplar in the active adapter's `exemplars/`. Read both before writing.

## Core idea

1. Doing good analysis ≠ writing a good report. A report is one act of communication; "rigor" is the analysis's requirement, "cognitive gain" is the report's — what cannot be understood yields no gain
2. Attention is finite. Stress five things and none is remembered; stress one and one is carried away
3. An analyst's impact comes almost entirely from one successful alignment on one analysis

Three questions before writing: who is the core audience (default: managers and partner teams)? what are they concerned about? what is the one conclusion I am presenting? Test: can the audience understand the conclusion in one minute and restate it, with its basis, to someone else in another minute?

## Outline before prose

Map the BRIEF hypothesis table to an outline (mapping in `references/structure.md`): section titles + one bold claim per section + which table each section carries. **The user approves the outline before any sentence is written.** A document destined for a publishing tool is drafted locally in full and imported whole; it is not assembled block by block.

## Writing rules

### 1. Full metric names, consistent throughout
A metric name carries its own qualifiers ("**cross-border report rate** (reports on cross-border traffic / impressions)", not "report rate"); the same metric keeps the same name everywhere; on first appearance give one plain-language sentence (standard in §3); field names and formulas stay in the SQL header block, not in the document.

### 2. Complete sentences, subject present
Every "higher / lower / up / concentrated" can answer "than what, under which definition". ❌ "report rate is higher than local, concentrated in the head" → ✅ "cross-border traffic's report rate is higher than local traffic's; the gap is concentrated in top producers".

### 3. Complex logic in three parts: define → visualize → one plain sentence
Define the groups / metrics / criteria before stating the conclusion, with a storyline between (how we grouped → which stages we looked at → what we found); one complex idea gets one chart or one simple table; every complex conclusion is followed by one sentence beginning "in other words, …" — if it cannot be said, it is not yet understood.

**"Plain language" means replacing jargon, not switching to slang.** All three must hold:
- vocabulary: everyday words in place of terms, abbreviations and coinages. Everyday ≠ colloquial — "decreased", "re-recommended" are everyday; "tanked", "went viral" are colloquial
- sentence: a complete subject–verb structure, not a fragment, exclamation or catchphrase. Clarity comes from completing the sentence, not from choosing a looser word
- register: written. Test: could the sentence be printed as-is in a formal report for a reader who does not know you

### 4. No abstract compounds, no invented or colloquial terms
- Explain with a sentence, do not compress into a noun stack: ❌ "followed-creator blended-feed exposure rate only 29%" → ✅ "70% of users had a followed creator live that day, but only 29% saw one in the blended feed"
- Deflate abstract verbs: "form cognitive alignment" → "agree"
- Coined compressions are forbidden; team-wide abbreviations (PV / UV / CTR) are fine; group names and headers state meaning + boundary ("US impressions 90–99% (19k–198k)", not "P4")
- Derived metrics coin words most easily: describe a quantity you constructed with a plain predicate first, shorten later
- Colloquialisms and hyperbole are forbidden everywhere: body, headers, group names, chart titles, appendix, chat interpretation (the adapter lists the team's offenders). Test: does the word map to a specific number or a falsifiable statement? The one exception is a **quotation**, in quotation marks with attribution
- Platform enumerations (category taxonomies, region names) keep their canonical spelling; readers match them against dashboards and the warehouse

### 5. Title = perspective, bold first line = conclusion; conclusion before data
- Section titles are perspective nouns ("report rate by audience region"); **the first line of every section is a bold conclusion sentence**, followed by 2–3 numeric bullets
- Each line in Conclusions is a complete sentence with its key number; hypotheses read "Hypothesis N: … ✅ holds, explains X% of the gap" or "❌ does not hold — criterion: holding category fixed, compare A with B". **Criterion before verdict**
- Numbers: differences as relative % ("36% higher") or percentage points (share gaps); multiples only at ≥2× ; explained share as "explains X% of the gap"; magnitudes with a reference ("0.4% of that day's total"); no pp differences on tiny-base rates

### 6. Evidence is a table under the claim; method lives where it is used
- **Under every bold claim: 2–3 numeric bullets + 1–2 tables or charts; every number in the claim is findable in the table.** The table is the citation; no parenthetical sources
- Definitions and data scope sit in the **section's opening quote block**, once (metric definitions, dates, regions; a missing region is named with its effect)
- **Notation, formulas and decision rules go in the section that uses them** (quote block + notation table, next to the table), not in the appendix
- The appendix holds the remaining slices; one bold claim before each table, or the table alone; the body references it in one sentence
- Self-test: reading only titles and bold lines, does the chain of reasoning hold? If not, the structure has a hole; words will not fill it

### 7. Background deserves care
When "why we are doing this" and "what good looks like" are not shared, the background explains them first; a topic with an obvious goal keeps it short.

### 8. Delete once more
For every line in Conclusions: does it help answer the audience's question? If not, delete. A report is not a work log.

## Tables and delivery files

- **Default one row per region plus one aggregate row** (`aggregate_row_label` in the adapter); a region that cannot be produced is omitted with the reason in the table note. Ratios: sum numerators and denominators, then divide; never average ratios across regions; medians and percentiles can only be weighted approximations, say so
- **Control-group / difference-in-differences columns stay out of body tables**: when control baselines barely differ across cells, three columns convey no more than one; the body shows the treated group's raw change, the baseline goes in a footnote; promote the control to a column only when its variation would flip the conclusion, and explain why
- **Data tables default to xlsx** (easy to edit and paste); visuals default to the adapter's document-tool-compatible HTML (inline styles, no CDN)
- **Every data table's last row is a provenance note**: definition summary + per-region query / file source
- **xlsx**: percent sign travels with the number in the cell (`number_format='0.0"%"'`, value stays 18.6), not in the header; rates store the raw value and let the number format control digits — no rounding before writing; **no cell text begins with `=`** (it becomes a formula)
- **Non-ASCII CSV is written with a UTF-8 BOM** (`encoding='utf-8-sig'`), or Excel mis-decodes it

## Publishing into the team's document tool

Adapter-specific commands live in the adapter's `delivery` reference. Core rules:
- **Change plan before touching an existing document; the user confirms**: list each change's location, content and reason; execute only what was confirmed. A brand-new document, or explicit line-by-line instructions from the user, may proceed directly
- **Fetch live before editing**: locate by current content, never by cached ids or memory
- **Data lands on disk before it enters the document**: results to CSV / xlsx under the topic directory first
- **Data tables as embedded spreadsheet blocks** (sortable, typed, color scales); small text tables may stay native; **read the header row before writing to a shared sheet**, address columns by name, append new columns on the right only

## Validators (deterministic; run before publishing)

- `python3 scripts/validate_doc.py <draft.md> --topic-dir <topic_dir> --report <out.md>`: structure, banned words, terms outside vocabulary, **every body number traced to a table**, sentence check. Errors must be zero
- `python3 scripts/validate_xlsx.py <table.xlsx|csv>`: `=` cells, rate formats, region + aggregate rows, provenance row, CSV BOM
- Vocabulary `<adapter>/vocab.txt`: the top half is generated by `scripts/build_vocab.py` from the adapter's references and exemplars; the bottom half (`# --- manual ---`) is hand-kept — a term the script flags that you judge to be everyday language goes there
- The `report-writer` agent runs both in draft and review; the main session runs them again on receipt as a second check

## Pre-delivery checklist

1. Can the audience grasp the conclusion from the summary in one minute?
2. Every metric has its full name and a plain-language sentence on first appearance?
3. Three random sentences: subject present, "than what" clear?
4. Every complex idea has definition + visual + one plain sentence?
5. No coinages, abstract compounds or colloquialisms? Group names and headers self-explanatory?
6. Every section is "bold claim + numeric bullets + table", numbers findable in the table?
7. Reading titles and bold lines only, does the argument hold? Notation lives in the section that uses it?
8. Nothing in Conclusions that does not help answer the question?
9. Every hypothesis in Conclusions has ✅/❌ + criterion + explained share? No medium/low confidence slipped in?
10. Outline approved by the user? Structure matches `references/structure.md`?
