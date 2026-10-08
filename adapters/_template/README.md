# Adapter template

Copy this directory, rename it, point `DS_HARNESS_ADAPTER_DIR` at it, fill the slots. Eight extension points, each a sub-directory; `adapter.json` is the index and is validated against `../../adapter-spec/adapter.schema.json`.

| Slot | Required | Fill |
|---|---|---|
| `platform/` | **yes** | `runbook.md` per region/engine; `checks.py` dialect rules; `setup.md` login and tooling |
| `compliance/` | no | `red-lines.md` (the one authoritative file); guard patterns in `adapter.json` |
| `channel/` | no | metadata-assistant script; Q&A channel commands; `secrets.json` (git-ignored) |
| `knowledge/` | recommended | `tables.md` with scope index; `metrics.md` definitions only; `glossary.md` |
| `analysis-priors/` | recommended | `domain.md` · `findings.md` (the workflow appends here) · `hypotheses.md` · `confounders.md` · `stances.md` |
| `delivery/` | **yes** | `conventions.md` for your document tool; `exemplars/` (two fictional ones ship here — replace them); `vocab.txt`; language word lists in `adapter.json → delivery.doc` |
| `operations/` | **yes** | workspace paths and ledgers in `adapter.json`; `guardrails.md` for headless sessions |
| `evals/` | no | `evals_cases.py`; `corrections.jsonl` |
| `skills/` `agents/` | no | team-only extensions installed alongside the core |

Full description: `../../adapter-spec/README.md`. Step-by-step: `../../docs/ADAPTER.md`.
