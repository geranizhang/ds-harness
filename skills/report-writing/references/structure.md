# Report structure

Distilled from finished reports that a team iterated to their final form against real data and real readers. **Structure follows this file**; where another rule conflicts, this file wins. The adapter's `exemplars/` directory holds the concrete reports; match the exemplar type to the question type before outlining.

## Skeleton

```
# Background       1–3 sentences: what observation prompted this, what we want to understand. Trend chart optional
# Conclusions      each line = complete sentence + key number. Hypotheses marked ✅ holds / ❌ does not + explained share.
                   High-confidence only
# <Perspective 1>  title is a perspective noun: "by audience region" / "source breakdown" / "supply vs distribution contribution"
  > definitions and scope (quote block): metrics used in this section, dates, regions
  **claim (bold)**: complete sentence + key number
  - 2–3 numeric bullets
  [table / chart] 1–2. Every number in the claim is findable here
  > notation table + formula (when the section uses a decomposition / counterfactual) — here, next to the table it explains
# <Perspective 2> …
# Case review      optional. Table: case × key metrics, with screenshots
# Appendix         remaining slices. One bold claim before each table, or the table alone
```

## Mapping from the brief

The hypothesis table in BRIEF.md is the document's skeleton, one to one:

| In the BRIEF | In the document |
|---|---|
| core question | Background |
| one hypothesis row (mechanism / if true / falsification) | one Conclusions line: "Hypothesis N: … ✅ holds, explains X%" or "❌ does not hold — criterion: …" |
| the queries hanging on one hypothesis | one perspective section; the table is those queries' result |
| known risks and blind spots | **not in the document**; stays in the BRIEF and the conversation |

Write the outline from this mapping (titles + bold claim per section + table per section); the user approves it before prose.

## Patterns the exemplars taught

Two report types recur. **Attribution** ("why is X different from Y"): hypotheses, verdicts, explained shares. **Survey** ("how big, where, how does it evolve"): descriptive, tiers and trajectories, judgments as degree words rather than ✅/❌. The patterns below say which type they apply to when it matters.

1. **The title is not the conclusion; the bold first line is.** Titles are perspective nouns for navigation; the first bold line of each section carries the finding.
2. **Method lives where it is used.** Section-level formulas, notation tables and decision rules sit as a quote block + table inside the perspective section. **Shared definitions and a whole reference-model method may take one appendix section** (prose derivation + formula + tiers + table); the body does not repeat it.
3. **Evidence is a table, not a parenthetical.** Each bold claim is followed by 2–3 numeric bullets and 1–2 embedded tables; the claim's numbers are checkable there. Scope and definitions are stated once in the section's opening quote block, not after every sentence.
4. **Alternative explanations appear as "❌ Hypothesis N does not hold"** in Conclusions, with one sentence of criterion and the number; there is no separate "alternatives and limitations" section.
5. **No confidence labels.** Only high-confidence conclusions are written; medium and low stay in the conversation and the BRIEF.
6. **No mandatory "recommendations" section.** When there is a clear action, one line; otherwise close with "further understanding … TBD".
7. **Numbers** — attribution: differences as relative % ("36% higher") or percentage points (share gaps); multiples only at ≥2×; explained share as "explains X% of the gap". **Survey: absolute shares and start→end raw pairs** ("0.84→0.89", "5→10→7"); pp and multiples may be absent.
8. **Criterion before verdict (attribution).** Every ✅/❌ is preceded by "criterion: holding category fixed, compare A with B". Survey reports omit the criterion sentence; the degree word carries it.
9. **Conclusions may be titled "TL;DR" and sub-divided by the body's chapters.** Each item = number + bold full-sentence claim (direction and verdict, no digits) + 1–3 unordered sub-bullets carrying all the digits (one more level allowed to split causes). A conclusion that *is* a numeric trajectory puts the digits in the claim and has no sub-bullets.
10. **Background may be a two-level question list.** One paragraph on the current state and what is unclear, one bold transition ("this document answers the following questions"), then a two-level ordered list of 2 main × 2 sub questions, each sub-question ending with `→` and the desired shape of the answer.
11. **Three or more heading levels use H1 chapter numbers, hand-numbered H2 sections, H3 perspectives.** H1 auto-numbers 1./2./3.; H2 is written 1.1 / 1.2; H3 is the perspective or population noun. Background, TL;DR and Appendix are unnumbered.
12. **Definition quote blocks have two levels.** Chapter-wide label systems and population definitions sit in a quote block under the H1 with a link to the upstream document; section-level quote blocks carry only the increment (observation window, tiering, extra metrics for this section).
13. **Charts side by side, not one per row.** 2 per row or 3–4 per row, each with a caption as its title; parallel sections (one per population) reuse the same chart slots and titles so readers compare across.
14. **Interactive chart or static table, not both.** When the evidence is a family of curves over n, use an interactive chart and no embedded table in that section; it may be followed by a one-line text caption and one static image.
15. **Change can be written as raw pairs, no conversion needed.** "0.84→0.89", "0.65→2.5" read faster than relative %; approximations take a "~" prefix; coined group names go in quotation marks with the definition at first use.
16. **Survey reports do not use ✅/❌ or explained share.** Judgments are degree words ("not a serious problem", "no visible issue", "severely insufficient") plus a `→` reserved inference ("→ exploration may be insufficient"). The reserved inference exists to surface a question for discussion: the section's data must point to it, the wording stops at "may", it is not written as cause or verdict, and it does not appear in TL;DR. ✅/❌ + criterion + explained share belong to attribution.
17. **Unfinished analysis gets its own chapter tagged tbd.** Title "<perspective> (tbd)"; body states the premise, the conjecture and numbered "what data is needed" questions; no numbers.
18. **A caveat sits next to the affected chart, followed by the corrected conclusion.** No "limitations" section: one sentence naming the bias, the next sentence in bold giving the conclusion under the corrected baseline.
