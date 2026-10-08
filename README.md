# ds-harness

A Claude Code plugin that takes a data-analysis question from hypothesis tree to a delivered report. The main session talks to the user and holds four human gates; three agents do the retrieval, the adversarial review and the writing; deterministic scripts check what can be checked by code; a hook blocks the irreversible mistakes in the environment. Everything specific to *your* data platform and team lives in an **adapter** with eight extension points — fill them and the generic harness becomes your team's workflow.

中文说明见 [README.zh.md](README.zh.md).

## What it does

```
question
  │ 🚪 gate one: which project does this belong to                 main session
  ├─ analysis-brief → BRIEF.md (hypotheses / dimensions / query list)   skill
  │ 🚪 gate two: execution plan (probes / regions / date split)     main session
  ├─ data-runner → raw/ + run report                                  agent   ← hook validates compliance SQL, blocks sampling
  ├─ verdict per hypothesis, back-filled into the BRIEF              main session   → findings.md
  ├─ adversarial-reviewer → challenges                                agent   (into BRIEF §5, never the document)
  ├─ report-writer(outline) → outline                                 agent
  │ 🚪 gate three: approve the outline                               main session
  ├─ report-writer(draft) → markdown + xlsx + validation              agent
  ├─ report-writer(review) → issue list                               agent
  │ 🚪 gate four: confirm the publish plan                           main session
  └─ publish, register the version                                   main session
```

Agents cannot ask the user mid-task; anything that needs a decision returns `BLOCKED` and the main session carries the answer back. Agents never edit the references; their findings return as "reference updates" that the main session writes down. A `qa-followup` agent, started by a chat daemon, answers colleagues' questions about delivered analyses within governance limits.

## The eight extension points

| Slot | Answers | Required |
|---|---|---|
| `platform` | how do we run a query here (regions, tools, fetch caps, dialect) | yes |
| `compliance` | what is forbidden and what is checked before submission | no |
| `channel` | how do we talk to catalog bots and chat channels | no |
| `knowledge` | what the data looks like (tables with scope index, metric definitions, glossary) | recommended |
| `analysis-priors` | what we already know (domain, settled findings, hypothesis library, confounders, stances) | recommended |
| `delivery` | how a report looks here (document tool, word lists, exemplars, vocabulary) | yes |
| `operations` | where files live and who may decide what (workspace, approvals, gates, guardrails) | yes |
| `evals` | how we know nothing regressed | no |

Specification: `adapter-spec/README.md`. Walkthrough: `docs/ADAPTER.md`. Skeleton with two fictional exemplar reports: `adapters/_template/`.

## Three layers of constraint

| Layer | What | Where |
|---|---|---|
| knowledge and flow | rules, definitions, exemplars — written for the model to follow | `skills/`, `agents/`, the adapter |
| deterministic checks | SQL header and sampling, raw-file truncation, every number in a report traced to a table, spreadsheet pitfalls | `skills/*/scripts/` |
| environment enforcement | compliance submissions validated on the spot; sampling blocked without approval | `hooks/guard.sh` |

The design question behind every rule: *is this enforced by the environment, or merely requested of the model?* Requested rules decay over a long session; the harness moves as many as it can into the lower two layers.

## Layout

```
adapter-spec/        README (the contract) · adapter.schema.json
adapters/_template/  skeleton: eight slots, two fictional exemplars
skills/              analysis-brief · analysis-workflow (+ analysis-patterns, workspace-conventions, validate_sql/raw)
                     report-writing (+ structure.md, validate_doc/xlsx, build_vocab) · _shared (adapter resolution)
agents/              data-runner · adversarial-reviewer · report-writer · qa-followup
hooks/               PreToolUse guard, configured by the adapter
evals/               validator regression · hook regression · corrections ledger tooling
bin/install.sh       install core + one adapter into ~/.claude as one workflow
docs/                DESIGN.md (core/adapter split) · ADAPTER.md (walkthrough)
```

## Install

```bash
git clone <this repo> ds-harness
cp -R ds-harness/adapters/_template /path/to/my-team      # fill it in (docs/ADAPTER.md)
ds-harness/bin/install.sh /path/to/my-team
```

The installer symlinks core skills, agents and the hook into `~/.claude`, links the adapter's own skills and agents beside them, and writes `~/.claude/ds-harness-adapter` so scripts and agents find the adapter without environment variables. Open a new session afterwards. `bin/install.sh --uninstall` reverses it.

Team adapters are private by design: keep yours in its own repository. `adapters/*` other than `_template` is git-ignored here.

Requirements: python3 (+ `openpyxl` for xlsx checks); your platform's query CLI; your document tool's CLI if you publish.

## Conventions

- Rule text carries no dates or attributions; the adapter's `CHANGELOG.md` records when and why a rule changed
- Dated **evidence** lives in `analysis-priors/findings.md`; the date tells a reader whether it is stale
- Each rule has one authoritative location; everywhere else points to it
- Changing a script or rule means running `evals/`

## Not included

Personal memory, project directories, document-tool skills, credentials, and the chat daemon that starts `qa-followup` (a long-running process kept outside the plugin).

## License

MIT — see `LICENSE`.
