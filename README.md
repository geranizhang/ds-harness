# ds-harness

A Claude Code plugin that takes a data-analysis question from hypothesis tree to a delivered report. The main session talks to the user and holds four human gates; three agents do the retrieval, the adversarial review and the writing; deterministic scripts check what can be checked by code; a hook blocks the irreversible mistakes in the environment. Everything specific to *your* data platform and team lives in an **adapter**.

中文说明见 [README.zh.md](README.zh.md).

## What it does

```
question
  │ 🚪 gate one: which project does this belong to                 main session
  ├─ analysis-brief → BRIEF.md (hypotheses / dimensions / query list)   skill
  │ 🚪 gate two: execution plan (probes / regions / date split)     main session
  ├─ data-runner → raw/ + run report                                  agent   ← hook validates compliance SQL, blocks sampling
  ├─ verdict per hypothesis, back-filled into the BRIEF              main session
  ├─ adversarial-reviewer → challenges                                agent   (into BRIEF §5, never the document)
  ├─ report-writer(outline) → outline                                 agent
  │ 🚪 gate three: approve the outline                               main session
  ├─ report-writer(draft) → markdown + xlsx + validation              agent
  ├─ report-writer(review) → issue list                               agent
  │ 🚪 gate four: confirm the publish plan                           main session
  └─ publish, register the version                                   main session
```

Agents cannot ask the user mid-task; anything that needs a decision returns `BLOCKED` and the main session carries the answer back. Agents never edit the references; their findings return as "reference updates" that the main session writes down.

## Three layers of constraint

| Layer | What | Where |
|---|---|---|
| knowledge and flow | rules, definitions, exemplars — written for the model to follow | `skills/`, `agents/`, `adapters/<name>/references/` |
| deterministic checks | everything that can be judged by code: SQL header and sampling, raw-file truncation, every number in a report traced to a table, spreadsheet pitfalls | `skills/*/scripts/` |
| environment enforcement | compliance submissions validated on the spot; sampling blocked without approval | `hooks/guard.sh` |

The design question behind every rule: *is this enforced by the environment, or merely requested of the model?* Requested rules decay over a long session. The harness moves as many as it can into the second and third layers.

## Layout

```
skills/
  analysis-brief/        question → hypothesis tree
  analysis-workflow/     the flow, four gates, dispatch; analysis-patterns, workspace-conventions; validate_sql / validate_raw
  report-writing/        structure and writing rules; structure.md; validate_doc / validate_xlsx / build_vocab
  _shared/               adapter resolution
agents/
  data-runner            retrieval: probe, parallel regions, truncation check, reconciliation, landing
  adversarial-reviewer   tries to overturn conclusions (read-only)
  report-writer          outline → draft + tables → independent review
  qa-followup            session-identity agent behind a chat channel: explain / re-slice / in-scope re-run / escalate
hooks/                   PreToolUse guard, configured by the adapter
evals/                   validator regression, hook regression, corrections ledger
adapters/
  _template/             copy this; ships with two fictional exemplar reports
docs/                    DESIGN.md (core/adapter split), ADAPTER.md (how to write one)
```

Team adapters are private by design: keep yours in its own repository and point `DS_HARNESS_ADAPTER_DIR` at it, or drop it under `adapters/<name>/` — everything there except `_template` is git-ignored.

## Install

As a plugin: add this repository as a marketplace, install `ds-harness`, set `DS_HARNESS_ADAPTER=<name>` (or `DS_HARNESS_ADAPTER_DIR=/abs/path`) in your shell. The hook mounts from `hooks/hooks.json`. For local development: `claude --plugin-dir <path>`.

As loose files: `skills/*` → `~/.claude/skills/`, `agents/*` → `~/.claude/agents/`, `hooks/guard.sh` → `~/.claude/hooks/`, and in `~/.claude/settings.json`:

```json
"hooks": {"PreToolUse": [{"matcher": "Bash|mcp__.*__run_command",
  "hooks": [{"type": "command", "command": "bash ~/.claude/hooks/guard.sh"}]}]}
```

Requirements: python3 (+ `openpyxl` for xlsx checks); your platform's query CLI; your document tool's CLI if you publish.

## Write your adapter

`docs/ADAPTER.md`. Short version: copy `adapters/_template`, fill `adapter.json`, write five reference files (platform, tables, metrics, glossary, delivery), drop in 1–3 exemplar reports, run `build_vocab.py`, run the evals.

## Conventions

- Rule text carries no dates or attributions; the adapter's `CHANGELOG.md` records when and why a rule changed
- Dated **evidence** stays in the references; the date is how a reader judges whether it is stale
- Each rule has one authoritative location; everywhere else points to it
- Changing a script or rule means running `evals/`

## Not included

Personal memory, project directories, document-tool skills, credentials, and the channel daemon that starts `qa-followup` (a long-running process, kept outside the plugin).

## License

MIT — see `LICENSE`.
