# Writing an adapter

An adapter teaches ds-harness about one data platform and one team. The core knows the *shape* of good analysis work; the adapter knows your tables, your regions, your compliance rules, your document tool, your vocabulary and what your team has already learned. The contract is `adapter-spec/README.md`; this page is the walkthrough.

## 1. Start from the template

```bash
cp -R adapters/_template /path/to/<your-team>      # outside this repo: adapters are private by design
python3 -c "import json; json.load(open('/path/to/<your-team>/adapter.json'))"
```

Keep `spec_version: "0.2"`, change `name`, `display_name`, `language`.

## 2. Fill the three required slots first

**platform** — `adapter.json → platform`: your regions (independent data partitions you query separately; one is fine), `default_regions`, the CLI or MCP server name, `fetch_limits` (the per-engine caps that silently truncate), `sql.header_markers` in your language, `sql.sampling_patterns`, `region_aliases` if people type different names than the CLI wants. Then `platform/runbook.md` per region (submit → poll → fetch, terminal states, failure signatures) and `platform/checks.py` with `sql_checks(sql, region) -> (errors, warnings)` for dialect rules.

**delivery** — `adapter.json → delivery.doc` holds everything `validate_doc.py` needs in your language: section names, forbidden sections, confidence-label regexes, colloquialisms, term suffixes, comparison words, number units. `delivery.tables` names the aggregate row and the region-column headers. `delivery/conventions.md` says how your document tool is driven. Drop 1–3 finished reports into `delivery/exemplars/` and describe their type in its README (the two fictional ones are placeholders — replace them). Run `build_vocab.py` to seed `delivery/vocab.txt`.

**operations** — `adapter.json → operations.workspace` (projects root, raw-file pattern, version-ledger columns, whether raw is committed) and `operations.governance` (approvals directory and TTL, which gates may be pre-authorized, what `qa-followup` may do alone and who approves the rest); `operations/guardrails.md` for daemon-started sessions.

At this point the workflow runs end to end on your platform.

## 3. Fill the recommended slots

**knowledge** — `knowledge/tables.md` *opens with a scope index* (global replica vs partitioned-by-region vs merged single source vs unverified); summing a global table across regions is the most expensive mistake this harness guards against. `knowledge/metrics.md` holds definitions only — five parts each. `knowledge/glossary.md` holds team shorthand and the default analysis scene.

**analysis-priors** — `domain.md` (how the system works), `findings.md` (settled conclusions; the workflow appends here at §5 and §6), `hypotheses.md` (recurring hypotheses and how they were tested), `confounders.md` (standard confounders, default dimensions, default control variable), `stances.md` (team choices: sampling default, region merging, estimation stance). Dated evidence that used to sit in a metric dictionary belongs in `findings.md`.

## 4. Optional slots

**compliance** — `compliance/red-lines.md` is the single authoritative statement of what is forbidden; `compliance.guard.submit_patterns` and `submit_region` make the hook validate submissions to that region on the spot. `compliance.guard.tests` lets `evals/run_hook_tests.sh` exercise your patterns.

**channel** — `channel.metadata_assistant` (a script that asks your catalog bot a factual question) and `channel/README.md` with the four `qa-followup` operations for your chat tool. Secrets go in env vars named in `channel.secrets_env` or in git-ignored `channel/secrets.json`.

**evals** — `evals/evals_cases.py` with `cases(ctx)` (one SQL that must fail your checks, one that must pass); `evals/corrections.jsonl` as your team's correction ledger.

**extensions** — team-only skills under `skills/<name>/SKILL.md` and agents under `agents/<name>.md`; the installer links them beside the core.

## 5. Install and verify

```bash
bin/install.sh --host claude-code --adapter /path/to/<your-team>    # or --host codex
DS_HARNESS_ADAPTER_DIR=/path/to/<your-team> python3 evals/run_validators.py
DS_HARNESS_ADAPTER_DIR=/path/to/<your-team> bash evals/run_hook_tests.sh
```

The host binding (`hosts/<host>/install.py`) links core and adapter skills, renders agents in the host's format, registers the hook and the tools declared in `platform.tools` (spec 0.3: `candidates`, `mcp_args`, `env`, `health_check`), and writes `~/.ds-harness/{adapter,host,harness}`; scripts, the hook and the agents resolve the adapter from that pointer on any host when no env var is set. Per-person values (projects root, approvals dir, secrets named in `channel.secrets_env`, a tool's local command) go in `~/.ds-harness/profile.json` (`adapter-spec/profile.schema.json`), never in the adapter. `bin/doctor.sh` checks the whole install.

## 6. Keep it alive

Three write-back targets: table facts → `knowledge/tables.md`; definitions → `knowledge/metrics.md`; conclusions → `analysis-priors/findings.md`. Rule changes get one line in the adapter's `CHANGELOG.md`; rule text carries no dates.
