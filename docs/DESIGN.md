# Design: core vs adapter

ds-harness was extracted from one team's working setup. This document records what moved where and why, so the boundary stays meaningful as both sides evolve.

## The one-sentence version

A **data-analysis harness for Claude Code**: the flow from question → hypothesis tree → retrieval → review → report → follow-up, the four human gates, three executing agents, deterministic validators and an environment-level guard are packaged as a plugin; **the data platform, compliance rules, exemplar reports and team vocabulary are an adapter**, never present in the core.

## The test for "core"

A rule belongs in the core if and only if it holds for *any* data team. Swap the team's platform names for another team's — is the rule still true? Yes → core. No → adapter.

| Content | Belongs to | Notes |
|---|---|---|
| four human gates; agents return `BLOCKED` instead of asking; agents never edit references | **core** | |
| hypothesis tree (mechanism / if true / falsification → verdict / explained share / evidence) | **core** | |
| fetch grain ≠ display grain; full data by default; verify fetched row counts; date-keyed merges | **core** | numeric caps live in the adapter's `fetch_limits` |
| data-source discovery as four priority levels (user → history → metadata assistant → catalog) | **core** (structure) / **adapter** (the tools at each level) | |
| three confidence tiers; high only in the document; adversarial review by an independent agent | **core** | |
| counterfactual decomposition, stratified standardization, same-tier control, adversarial checklist | **core** | |
| report skeleton (background → conclusions → perspectives → appendix); bold first line; method where it is used | **core** (skeleton, 18 patterns) / **adapter** (the exemplar reports themselves) | the template ships two fictional exemplars |
| no invented or colloquial terms; "plain language" as three conditions; number formatting | **core** (rules) / **adapter** (the word lists, in the team's language) | |
| vocabulary whitelist | **adapter**; the core ships the generator | |
| region/engine runbooks, queues, fetch caps, login, compliance red lines | **adapter** | the core ships `platform.md` as a template |
| table handbook, metric dictionary, glossary | **adapter**; the core ships templates with the required shape (scope index; rules vs dated evidence) | |
| metadata-assistant script (ask an internal catalog bot) | **adapter**; the core names the interface | |
| document-tool conventions | **adapter**; the core states the gate and the generic rules | |
| guard hook: validate on submission, block sampling without approval | **core** (mechanism) / **adapter** (which commands, which region, which validator) | the hook reads `adapter.json → guard` |
| `validate_sql` | **core** (header block, sampling, in-SQL binning) / **adapter** (`checks.py`: dialect and compliance) | |
| `validate_raw` / `validate_doc` / `validate_xlsx` / `build_vocab` | **core**; file patterns, section names, word lists and region columns come from `adapter.json` | |
| `qa-followup` (classification, boundaries, reply format) | **core**; channel operations are an interface the adapter implements; the daemon that starts it lives outside the repository | |
| regression suite | **core**; an adapter may add `evals_cases.py` for its own dialect rules | |
| corrections ledger | **core** (format and scripts); a team's cases are private | |

## Resolution

- `DS_HARNESS_ADAPTER_DIR=/abs/path`, else `DS_HARNESS_ADAPTER=<name>` (→ `<plugin root>/adapters/<name>`), else the path in `~/.claude/ds-harness-adapter` (written by `bin/install.sh`), else `_template`
- Adapter spec 0.2: `adapter.json` is nested by the eight extension points (`adapter-spec/README.md`); agents and scripts read it by dotted path (`knowledge.tables`, `delivery.doc`, …), never by guessing filenames
- Scripts and the hook read `adapter.json`; with the template adapter every platform check degrades to "fill in your adapter"
- `adapters/*` except `_template` is git-ignored: a team's adapter is private by design and lives in its own repository

## Deliberate limits

1. Exemplars are the structural authority for `report-writer`. The two shipped are fictional; a team should replace them with its own finished reports.
2. `validate_doc`'s English mode flags abbreviations, identifiers and suffix phrases as "terms", not every word; its Chinese mode (`cjk_suffix_terms`) flags every ASCII token because CJK prose has no word boundaries. Other scripts are untested.
3. The harness decomposes; it does not identify causes. Experiments remain the gold standard, and the agents are told to say so.
4. No agent-level regression yet (does `data-runner` stop where it should on a given brief). The validator and hook suites cover the deterministic layer only.
