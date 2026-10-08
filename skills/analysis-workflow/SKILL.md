---
name: analysis-workflow
description: End-to-end data-analysis workflow for a team — take any analysis question from hypothesis tree to a deliverable report, with data retrieval, adversarial review and report writing delegated to agents and four human gates kept in the main session. Use when the user raises a data-analysis question, needs to find a data source or metric definition, wants a query run on the team's platform, or wants numbers interpreted. Platform rules, table handbooks and compliance constraints come from the active adapter (DS_HARNESS_ADAPTER).
---

# Analysis workflow

The main session is the **dispatcher**: it talks to the user, holds the four human gates, hands retrieval and writing to agents, and writes agents' findings back into the references. **Rules live in the adapter's references and in the agents; this file is the flow only.** The less familiar the question, the more strictly the first three steps apply.

## Where things live

| Location | Content | Main reader |
|---|---|---|
| `<adapter>/references/` (via `adapter.json → references`) | platform runbook(s), table handbook with **scope index**, metric dictionary, glossary, delivery conventions | agents and the main session |
| `references/analysis-patterns.md` | attribution toolkit, analysis discipline, three confidence tiers, adversarial checklist | main session §5, `adversarial-reviewer` |
| `references/workspace-conventions.md` | directory skeleton, provenance, version ledger, git | every role |
| `scripts/` | `validate_sql.py`, `validate_raw.py` — deterministic checks the runner must pass | `data-runner`, main session |

`<adapter>` resolves from `DS_HARNESS_ADAPTER_DIR`, else `<harness>/adapters/$DS_HARNESS_ADAPTER`. Without an adapter the flow still runs, but every platform-specific check reports "fill in your adapter". What the references do not contain does not mean it does not exist — go through §2 and write back what you find.

## Roles

| Role | Shape | Input → output |
|---|---|---|
| main session | this skill | the user's question → four gates + dispatch + write-back |
| `analysis-brief` | skill | question → BRIEF.md (hypothesis tree: question / hypotheses / dimensions / query list) |
| `data-runner` | agent | approved plan + query list → raw files + structured run report |
| `adversarial-reviewer` | agent | conclusions → challenges (not for the document) |
| `report-writer` | agent | BRIEF → outline → draft + tables → review report |
| `report-writing` | skill | structure and writing rules; the main session follows them when publishing |
| `qa-followup` | agent (session identity) | delivered analysis + a chat channel → follow-up answers; needs an adapter channel implementation |

Agents cannot ask the user mid-task: anything needing a decision comes back as `BLOCKED`; the main session asks, then hands the answer to **the same agent**. Agents do not edit references; their "reference updates" are written by the main session in the same turn.

## Flow

### 0. Preflight
Confirm the platform tooling the adapter's `setup`/`platform` reference names is reachable and the session is valid. An auth error stops and asks the user; never route around it.

### 1. Clarify 🚪 gate one: where the question lives
- List existing projects and their topics (each `PROJECT.md`); ask "new project, or under X?"; on confirmation create `topics/<YYYYMM_slug>/` per `workspace-conventions.md` and register it
- An unfamiliar or complex question goes through `/analysis-brief` first; align the BRIEF with the user before continuing
- Confirm every metric's five parts (meaning / source field / numerator-denominator / aggregation / approximation error); when the meaning is unclear, ask, never assume
- Confirm scope: dates, product surface, regions, traffic source, population; restate the question as one falsifiable sentence

### 2. Data-source discovery
**Strict priority; stop at the first level that resolves.** Every candidate from any level is probed (enumeration values / volume / partition readiness) before use, then added to the adapter's `tables.md` (**fill the scope column**). Conflicting candidates go to the user with the differences; do not pick.

1. **The user named it** — use the table / column / dataset they named; ask on ambiguity, never substitute "something better"
2. **Used before** — `tables.md` entries, `topics/*/raw/` sibling SQL, saved query templates, past documents, existing dashboards (if a dashboard answers it, write no SQL)
3. **Metadata assistant** — if the adapter provides `metadata_assistant`, ask it factual questions (which table has X, meaning of column Y, where dataset Z is, partitions and TTL). Treat the reply as an **external claim**: use only after DESCRIBE / partition listing / a probe reproduces it; tag the `tables.md` entry "assistant + probe-verified <date>". Definition *choices* are never asked of it
4. **Catalog search** — the warehouse catalog, lineage, production job scripts; whichever path is reachable; do not search everything for completeness

### 3. Execution plan 🚪 gate two
Before any query, state three things at once and wait for confirmation: ① probe plan (probe or not, what, which doubt each resolves); ② how tasks are built per region and where the SQL differs; ③ how multi-day ranges are split. If the user confirms part, run only that part. Default: every region in `default_regions` in parallel; compliance regions follow the adapter's red lines.

### 4. Retrieve → `data-runner`
Prompt with `topic_dir`, `plan` (marked "user approved"), `queries` (BRIEF §4 rows), `date_range`, `regions`.
- `BLOCKED` → ask the user, hand the answer with the original prompt back to the same agent
- `DONE` / `PARTIAL` → read the Validation block first (`validate_sql` / `validate_raw` must be clean), then reconciliation and "not obtained", then §5
- The PreToolUse hook validates compliance-region submissions and blocks sampling; after the user explicitly approves sampling, the main session touches the approval file named in `adapter.json → guard.approvals_dir`
- **Fetch grain ≠ display grain**: the runner lands entity-level raw with original dimension values and additive measures; binning, top-N and ratios happen in §5 locally. If a raw file arrives already aggregated to the BRIEF's display grouping, send it back — its bin edges cannot be changed

### 5. Analyze and review
Per `analysis-patterns.md`: for each hypothesis apply the criterion written in the BRIEF beforehand, give ✅ / ❌ / partial plus the explained share, and back-fill the hypothesis table's last three columns. Then call `adversarial-reviewer` (topic dir + conclusions) and answer each challenge — more data where possible, a lower tier otherwise. Three confidence tiers; **only high confidence enters the document**; medium and low go to BRIEF §5 and are discussed with the user.

### 6. Deliver → `report-writer` 🚪 gates three and four
1. `report-writer` `mode: outline` → outline + "not in document" list → **🚪 the user approves the outline**
2. `mode: draft` (`approved_outline` marked "user approved") → local markdown + xlsx + validation report
3. `mode: review` → independent issue list → the main session edits the draft accordingly
4. Publish: produce a change plan per `report-writing` → **🚪 the user confirms** → execute through the adapter's delivery conventions; a new document is imported whole, not assembled block by block
5. Register: deliverable version, versions.csv, git commit (`workspace-conventions.md`); when a definition changed, update documents that carry the old numbers

## Maintenance

New table gotchas, new definitions, platform behavior changes, a reference proven wrong — **update the file at once**; delete what is wrong rather than keeping both versions. The agents' "reference updates" are the only channel through which their knowledge returns; do not drop them. A rule change gets one line in the adapter's `CHANGELOG.md` (date and reason live there; rule text carries no dates).

### Logging corrections
When the user overrides or rewrites something at a gate, during acceptance of an agent's output, in delivery polish or in a follow-up, log one case with `evals/corrections/log_correction.py` (see its README for `kind`: explore / tweak / violation / generalize). The ledger is not a rulebook; `review.py` surfaces candidates and the user decides what becomes a rule.
