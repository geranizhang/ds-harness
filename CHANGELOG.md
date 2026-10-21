# CHANGELOG — core

Rule text in the core carries no dates; when and why a rule changed is recorded here. Adapter rule changes go in the adapter's own `CHANGELOG.md`.

## 0.2.0 — 2026-10

- Adapter spec 0.2: eight explicit extension points (platform, compliance, channel, knowledge, analysis-priors, delivery, operations, evals) plus extensions; `adapter-spec/` carries the contract and a JSON schema; `adapter.json` is nested by slot and read through `harness_config.get()`.
- New slot `analysis-priors`: domain research, settled findings (the workflow's write-back target at §5/§6), hypothesis library, confounders and default dimensions, team stances. Dated evidence moves here from the metric dictionary.
- Team stances removed from core discipline (`analysis-patterns.md`): the estimation stance (point vs upper bound) and the sampling default are adapter choices; the core keeps the mechanisms.
- `report-writer` no longer checks for a "user approved" marker in draft mode; gate three is the main session's responsibility. Reading list is per mode. Reserved inferences allowed in the body under three conditions (not in TL;DR).
- `bin/install.sh`: installs core + one adapter into `~/.claude` as one workflow and writes `~/.claude/ds-harness-adapter`; scripts, hook and agents resolve the adapter from that pointer when no env var is set.
- Template adapter restructured into the eight slots; two fictional exemplars live under `delivery/exemplars/`.

## 0.1.0 — 2026-10

- Extracted from a single-team setup (that team's adapter lives in its own private repository). Core/adapter split: flow, gates, agents, validators and hook are core; platform runbooks, table handbook, metric dictionary, exemplars, vocabulary and channel scripts are adapter.
- Agents renamed: `sql-artist` → `data-runner`, `doc-reporter` → `report-writer`. Skills renamed from the originating team's names to `analysis-workflow`, `analysis-brief`, `report-writing`.
- All validators read `adapter.json`; dialect and compliance checks moved to the adapter's `checks.py`; the guard hook reads the adapter's guard section.
- Core text in English; adapter content keeps its team's language.
