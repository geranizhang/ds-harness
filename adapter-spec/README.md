# Adapter specification (spec 0.2)

An **adapter** turns the generic harness into one team's workflow. It is a directory with an `adapter.json` index and eight sub-directories, one per extension point. The core never contains anything from any one company; everything a company needs to plug in has a slot here.

Resolution: `DS_HARNESS_ADAPTER_DIR=/abs/path` (preferred for private adapters), else `DS_HARNESS_ADAPTER=<name>` under `<harness>/adapters/`, else `_template`. `adapter.json` is validated against `adapter.schema.json` by `harness_config.load()`.

## The eight extension points

| # | Extension point | Question it answers | Required? | Consumers |
|---|---|---|---|---|
| 1 | **platform** | How do we run a query here? Regions, tools (CLI / MCP), submit → poll → fetch, fetch caps, SQL dialect rules, login | **required** | `data-runner`, `validate_sql`, guard |
| 2 | **compliance** | What is forbidden, and what gets checked before it leaves the machine? Red lines (one authoritative file), registered output columns, which commands are guarded | optional | guard hook, `data-runner`, `validate_sql` |
| 3 | **channel** | How do we talk to people and bots? Metadata assistant (ask the catalog bot), Q&A channel operations, which secrets the scripts need | optional | workflow §2, `qa-followup` |
| 4 | **knowledge** | What does the data look like? Table handbook with **scope index**, metric dictionary (definitions only), glossary | strongly recommended | all agents, main session |
| 5 | **analysis-priors** | What have we already learned? Domain research, settled findings, hypothesis library, standard confounders and dimensions, analytic stances | strongly recommended | `analysis-brief`, `adversarial-reviewer`, `report-writer`, `qa-followup`, `data-runner` |
| 6 | **delivery** | How does a report look here? Document-tool conventions, presentation rules, exemplar reports, vocabulary, language-specific word lists and number units | **required** | `report-writer`, main session gate four, `validate_doc`, `validate_xlsx` |
| 7 | **operations** | Where do files live and who may decide what? Workspace layout and ledgers; approvals, gate policy, headless guardrails | **required** | every role, `validate_raw`, guard |
| 8 | **evals** | How do we know nothing regressed? Adapter regression cases, the team's corrections ledger | optional | `evals/run_validators.py` |

Plus:
- **extensions** — team-only skills and agents installed alongside the core (`skills/`, `agents/` inside the adapter)
- **secrets** — not an extension point but a rule: ids, tokens, endpoints go in env vars or a git-ignored `channel/secrets.json`; never in tracked files, even in a private repository

## Directory layout

```
<adapter>/
  adapter.json                  index; validated against adapter.schema.json
  platform/   runbook(s).md · setup.md · checks.py
  compliance/ red-lines.md · column-pool.md
  channel/    README.md (ops) · metadata assistant script · secrets.json (git-ignored)
  knowledge/  tables.md · metrics.md · glossary.md
  analysis-priors/ domain.md · findings.md · hypotheses.md · confounders.md · stances.md
  delivery/   conventions.md · exemplars/ · vocab.txt
  operations/ guardrails.md
  evals/      evals_cases.py · corrections.jsonl
  skills/ agents/               extensions
  CHANGELOG.md                  when and why a rule in this adapter changed
```

## How knowledge flows back

The core writes into the adapter at three points, always via the main session (agents never write references):
- new table facts → `knowledge/tables.md` (fill the scope column)
- new metric definitions → `knowledge/metrics.md`
- settled conclusions, verdicts, dated evidence → `analysis-priors/findings.md` (workflow §5/§6)

`knowledge` is *what the data is*; `analysis-priors` is *what we know about the domain*. Dated evidence belongs in priors, not in the metric dictionary.

## Degradation

With the template adapter the workflow still runs: `validate_sql` warns that no dialect checks are loaded, the guard enforces nothing platform-specific, `report-writer` uses the two fictional exemplars, and `analysis-brief` falls back to the generic dimension taxonomy. Every message that results from an unfilled slot names the slot.

## Writing one

See `../docs/ADAPTER.md` for a step-by-step guide and `../adapters/_template/` for a filled-in skeleton.
