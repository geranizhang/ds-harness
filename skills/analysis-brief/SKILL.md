---
name: analysis-brief
description: Turn an analysis question into an analysis brief — what question is being answered, which hypotheses, which dimensions matter, exactly which numbers to pull. Use when the user raises an analysis topic and wants a plan or framework before running anything, wants to align on analysis design, or asks "how should this be analyzed".
---

# Analysis brief

Covers **before any query runs**: turn a topic into a brief the team can align on and execute. Neighbouring pieces: `analysis-workflow` executes (source discovery, retrieval, review); `report-writing` turns conclusions into a document.

The output is one **BRIEF.md** — the hypothesis tree (mind map) for this topic. It lives at `<projects>/<project>/topics/YYYYMM_<slug>/BRIEF.md` (directory conventions in `analysis-workflow/references/workspace-conventions.md`) and is aligned with the user before anything runs. The analysis then walks the tree hypothesis by hypothesis; the report's Conclusions section is the verdict on each node (mapping in `report-writing/references/structure.md`).

## Four steps

### 1. What question is being answered
- **Whose question is it**: the core audience and the decision they must make (invest or not, ship or not, govern whom)
- **Rewrite the topic as one falsifiable question** ("is / why is X higher than Y"); split complex topics into 2–4 sub-questions, each answerable on its own
- **What counts as answered**: write the decision criterion before running. **It must be numeric**: set the threshold if it can be set ("gap ≥ 20%"); if it depends on a probe, name the probe, the output and the rule ("the P75 of matrix A3's cross-language views is the waterline"). A bare "decide after probing" is not allowed
- **Scope**: dates, regions, product surface, traffic source, population. Ask about anything vague; do not assume

### 2. Hypotheses
Start from the adapter: `analysis_priors.hypotheses` (recurring hypotheses for this class of question and how they were tested), `analysis_priors.findings` (what is already settled — cite, do not re-test), `analysis_priors.domain` (how the system works). Then every hypothesis carries three parts, none optional:

| Part | Form |
|---|---|
| mechanism | one sentence of causal chain ("because A, therefore B") |
| if true, what the data looks like | the observable shape (which group is higher / which curve moves) |
| how to falsify | what observation rules it out |

After the analysis, three more columns are back-filled **in the BRIEF itself, not a new file**: **verdict** (✅ holds / ❌ does not / partial, with one sentence of criterion), **explained share** (explains X% of the gap), **evidence table** (which raw / deliverable). These three columns map one-to-one to lines in the report's Conclusions.

- The list must **cover the opposition**: beyond "what I suspect", include at least a confounder (Z drives both grouping and metric), a definition artifact (numerator or denominator mechanically favors a group) and a measurement blind spot (detection coverage uneven; "cleaner" may be "undetected")
- Attribution questions use the toolkit in `analysis-workflow/references/analysis-patterns.md`; do not reinvent it

### 3. Dimensions
Walk the team's taxonomy in `analysis_priors.confounders` (default dimensions, standard confounders, default control variable) and write **why each chosen dimension might carry signal** (which hypothesis it hangs on); never split for the sake of splitting. The generic list below is the fallback when the adapter has none:

- demand side: region / country, user tiers (activity / tenure / age)
- supply side: producer region / country, producer tiers (popularity / quality / lifecycle)
- content: category, language, tags
- distribution: entry point / channel, matching pairs (consumer country × producer country)
- time: trend, before/after an event, time of day
- structure: concentration (a few heavy units or systemic), Simpson check (total gap vs within-group direction)

Keep dimensions that separate at least two hypotheses; those that only make the picture "finer but no different" go to the appendix or are cut.

### 4. Exactly which numbers
Turn hypotheses × dimensions into a **query list**. Standard of specificity: **the person executing can write the SQL without coming back to ask.** Self-test each row: ① what does this number answer (which sub-question / hypothesis, which clause of the criterion); ② what is pulled (table, columns, filters, grouping, comparison); ③ what is the definition (five parts, to the column). Any unanswered question fails the row.

Each row carries:

| Column | Content | Specificity |
|---|---|---|
| # | priority order | — |
| verifies | which hypothesis / sub-question | also "which output number meets which clause of the criterion"; a query that hangs on nothing is deleted |
| source | table | **table + key columns + filters**; a "to be found" must come with the finding action (where, keywords, what to confirm) |
| metric | five-part definition | meaning / source field / numerator-denominator / aggregation / approximation error, **all written**, source to `table.column`; row-specific filters stated inline even when the definitions block covers the metric |
| **fetch grain** | what SQL pulls | **entity level + raw dimension values + additive measures** (e.g. `entity_id × date × country_code`, sums of views / reports). Binning, top-N, ratios, region mapping and long-tail merges **do not belong here** — they go in the next column |
| **display grouping** | how it is cut locally | column names plus the collapse rules (top N, whitelist, tail merge, bin edges). This column can change during analysis without a re-run |
| comparison | against what | the control's filters (local baseline / same-tier control / time control, as a concrete slice) |
| expected output | what table or chart | a **header-level mock** (list the columns) and one sentence on how it serves the criterion |

Order: **cheap first** — probes (enumerations / volume baselines / partition readiness), then overview decompositions, then expensive work (stratified standardization / event studies); early results may cut half the list. State which probe result would cut or rewrite which rows.

## Pre-handoff checklist

1. Every query hangs on a hypothesis (none → delete)
2. Every hypothesis has a falsification path (none → it is a belief, not a hypothesis)
3. The opposing explanations (confounder / definition / measurement) are in the list
4. The criterion is written before the run and is numeric or "probe X, rule Y" (no post-hoc criteria)
5. Nothing in scope or definitions is "my guess" (if so, ask first)
6. Every query row: could the executor write SQL from it? (source has table and columns; five-part metric complete; fetch grain is entity-level raw; display grouping and comparison down to filters; expected output has a header mock)
7. (at the end of the analysis) back-filled verdict / explained share / evidence table on every hypothesis, each ✅/❌ with its criterion

## BRIEF template

```markdown
# <topic> — analysis brief
- Audience and decision:
- Data scope: dates / regions / surface / traffic source

## 0. Metric definitions (one block for the whole document; five parts each: meaning / source(table.column) / numerator-denominator / aggregation / approximation error)

## 1. Core question
- Main question (falsifiable):
- Sub-questions:
- Decision criterion (numeric, or "probe X, rule Y"):

## 2. Hypotheses (first four columns before running; last three back-filled after)
| # | hypothesis (mechanism) | if true, data looks like | how to falsify | verdict + criterion | explained share | evidence table |

## 3. Dimensions
| dimension | hangs on hypothesis | why it might carry signal |

## 4. Query list (priority order; every row translates straight to SQL)
| # | verifies (criterion clause) | source (table+columns+filters) | metric (five parts / ref block + inline deltas) | fetch grain (entity × raw dims × additive measures) | display grouping (local cuts) | comparison (concrete slice) | expected output (header mock) |

## 5. Known risks and blind spots (not for the document)
(confounders / definition artifacts / measurement blind spots / data availability; adversarial challenges and responses; medium- and low-confidence conclusions — all of this stays here and in conversation; the document carries high-confidence conclusions only)
```
