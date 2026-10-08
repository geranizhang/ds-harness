# Writing an adapter

An adapter teaches ds-harness about one data platform and one team. The core knows the *shape* of good analysis work; the adapter knows your tables, your regions, your compliance rules, your document tool and your team's vocabulary.

## 1. Copy the template

```bash
cp -R adapters/_template adapters/<your-team>
export DS_HARNESS_ADAPTER=<your-team>        # or DS_HARNESS_ADAPTER_DIR=/abs/path
```

## 2. Fill `adapter.json`

| Key | Meaning | Used by |
|---|---|---|
| `regions`, `default_regions` | independent data partitions you must query separately (data centers, shards, tenants). One region is fine | data-runner, validate_xlsx, run_validators |
| `aggregate_row_label`, `region_column_names` | the "all regions" row label and the header names that mark a region column | validate_xlsx, report-writer |
| `raw_name_pattern` | regex for raw file names; must end in `_<REGION>.csv` | validate_raw |
| `fetch_limits` | per-engine caps that silently truncate; the runner splits queries rather than aggregating | data-runner |
| `sql.header_markers`, `sql.header_lines` | words that must appear in a SQL header block (goal / definition / scope, in your language) | validate_sql, guard |
| `sql.sampling_patterns` | regexes that identify sampling | validate_sql, guard |
| `sql.dialect_checks` | path to `checks.py` with `sql_checks(sql, region) -> (errors, warnings)` | validate_sql, guard |
| `sql.region_aliases` | maps the names people type to the names your CLI wants | validate_sql |
| `doc.*` | section names, forbidden words, confidence-label regexes, term suffixes, comparison words, number units — everything `validate_doc.py` needs to work in your language | validate_doc, build_vocab |
| `guard.command_patterns` | what your data CLI looks like on a command line (bare name, `node …/cli.js`) | guard |
| `guard.submit_patterns`, `guard.submit_region` | which commands are submissions to a compliance-bound region; the guard validates their `--query-file` on the spot | guard |
| `guard.approvals_dir`, `guard.approval_ttl_seconds` | where the main session touches `sampling` after the user approves, and for how long it counts | guard |
| `metadata_assistant` | optional script: ask your internal catalog bot a factual question, print its reply | workflow §2 step 3, data-runner |
| `references` | logical name → file; agents read through this map (`platform`, `tables`, `metrics`, `glossary`, `delivery`, plus any region-specific extras) | every agent |

## 3. Write the references

The templates under `_template/references/` show the shape. Three conventions matter more than the rest:

- **`tables.md` opens with a scope index** — global replica vs partitioned-by-region vs merged single source vs unverified. The single most expensive mistake this harness guards against is summing a global table across regions.
- **`metrics.md` separates rules from dated evidence.** A rule has no date. "On 2026-08-12 we observed X" has one, and that date is how a later reader knows whether to trust it.
- **Compliance red lines have one authoritative location** (usually the top of the compliance region's platform runbook). Agents link to it; they do not restate it.

## 4. Exemplars and vocabulary

Put 1–3 finished reports in `exemplars/` and describe their type in `exemplars/README.md`. Then `python3 skills/report-writing/scripts/build_vocab.py` generates the top half of `vocab.txt`; keep team-accepted words that the generator misses under `# --- manual ---`.

Exemplars are usually internal. If you publish your adapter, strip them and keep the README.

## 5. Channel (optional, for `qa-followup`)

`qa-followup` needs four operations: `ack`, `reply_in_thread`, `dm_owner`, `read_document`. Put the concrete CLI calls in `channel/README.md` and the daemon that starts the agent outside this repository (it is a long-running process, not a plugin component).

## 6. Run the regressions

```bash
DS_HARNESS_ADAPTER=<your-team> python3 evals/run_validators.py
DS_HARNESS_ADAPTER=<your-team> bash evals/run_hook_tests.sh     # only if you set guard.submit_patterns
```

Add a `case_adapter_<name>` to `run_validators.py` for your own dialect checks: one bad SQL that must fail, one good SQL that must pass.
