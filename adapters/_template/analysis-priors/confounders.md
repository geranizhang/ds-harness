# Standard confounders and default dimensions (template)

## Confounders to walk, one by one, before calling a gap causal

| Confounder | Why it could drive both selection and outcome | Pre-determined proxy |
|---|---|---|
| popularity / size | | |
| category | | |
| geography | | |
| time of day / seasonality | | |
| lifecycle / tenure | | |

The proxy must be fixed *before* exposure to the treatment, or stratifying on it over-controls.

## Default dimension taxonomy (what `analysis-brief` §3 walks)

- demand side: …
- supply side: …
- content: …
- distribution / channel: …
- time: …
- structure: concentration, Simpson check

## Default control variable

When the brief needs "overall user engagement" held fixed: which table, which column, which snapshot date.
