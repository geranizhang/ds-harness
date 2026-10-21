# CHANGELOG — core

Rule text in the core carries no dates; when and why a rule changed is recorded here. Adapter rule changes go in the adapter's own `CHANGELOG.md`.

## 0.3.0-dev (unreleased)

- Spec 0.3: `platform.tools` declarations (`candidates` / `mcp_args` / `env` / `health_check`) registered and health-checked by the host binding, `harness_config.tool_exec(name)` for adapter scripts; per-person profile `~/.ds-harness/profile.json` with an allow-list (workspace, approvals dir, declared secrets, per-tool overrides) applied by `harness_config.load()` and the guard; `knowledge.sources` registry; `bin/doctor.sh`; `adapter-spec/profile.schema.json`. 0.2 adapters still load.
- Host bindings: `hosts/<host>/host.json` + `install.py` (claude-code, codex); `bin/install.sh --host <h> --adapter <dir>` is the one entry point and `bin/install-codex.sh` is gone; `hosts/verify.py` checks an install. One pointer directory `~/.ds-harness/{adapter,host}` for every host; 0.2 pointers still read. `platform.tools` may be a list of declarations (spec 0.3 draft: command / args / env / resolve / health_check) that the host registers; the 0.2 two-name form still works. Design: `docs/ARCHITECTURE-0.3.md`.
- Claim ladder (descriptive / decomposition / causal), selection mechanism and generating-stories table in `analysis-brief`; `validate_doc` check F; adversarial-reviewer audits them; strip-top-1% recompute.

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
