# CHANGELOG — core

Rule text in the core carries no dates; when and why a rule changed is recorded here. Adapter rule changes go in the adapter's own `CHANGELOG.md`.

## 0.1.0 — 2026-10

- Extracted from a single-team setup (that team's adapter lives in its own private repository). Core/adapter split: flow, gates, agents, validators and hook are core; platform runbooks, table handbook, metric dictionary, exemplars, vocabulary and channel scripts are adapter.
- Agents renamed: `sql-artist` → `data-runner`, `doc-reporter` → `report-writer`. Skills renamed: `tt-live-analytics` → `analysis-workflow`, `ds-report-structure` → `analysis-brief`, `data-report-docing` → `report-writing`.
- All validators read `adapter.json`; dialect and compliance checks moved to `adapters/<name>/checks.py`; the guard hook reads `adapter.json → guard`.
- Core text in English; adapter content keeps its team's language.
