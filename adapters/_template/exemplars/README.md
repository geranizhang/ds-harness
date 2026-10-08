# Exemplars

Two fictional reports (fictional marketplace, fictional numbers) that follow `skills/report-writing/references/structure.md`. Replace them with 1–3 finished reports your own team considers the standard, and keep this table current: `report-writer` reads the exemplar matching the report type before every outline, and `build_vocab.py` treats words used here as accepted vocabulary.

| File | Type | When to compare against it |
|---|---|---|
| `01_attribution_long.md` | multi-hypothesis attribution, long | "why is X different from Y" — hypotheses with criterion → ✅/❌ → explained share; a decomposition with its notation next to the table it explains |
| `02_survey_short.md` | survey / sizing, short | "how big is X, whom does it reach, how does it evolve" — TL;DR with numbered bold claims and digits in sub-bullets, degree words instead of ✅/❌, raw start→end pairs, a `(tbd)` chapter for unfinished work |

Both pass `validate_doc.py` against this template adapter: every number in body text is findable in a table in the same section.
