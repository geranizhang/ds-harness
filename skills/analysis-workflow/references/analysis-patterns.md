# Analysis methods and discipline

For any question of the form "why does group / policy X differ from Y on metric M". Metric definitions live in the adapter's `metrics.md`; writing rules in `report-writing`.

## Analysis discipline (before running and before concluding)

These hold for any team. Team-specific *choices* (sampling default, how regions are combined, whether impact estimates take a point or an upper bound, parallel vs serial execution) are not here; they live in the adapter's `analysis_priors.stances` and the agents read them.

1. **Sampling is a decision, not a shortcut.** Row-level sampling predicates filter after the scan and save no I/O; they trade certain precision loss for unverified gain. Whatever the team's default, the analyst never introduces sampling on their own — the guard blocks it without an approval
2. **No invented populations.** Use the population the user specified; intermediate groups created to validate a definition are discarded after use and leave one footnote, never promoted to a "finding". Before adding a population dimension, state why the existing one does not answer the question and wait; before calling a new population "worth attention", compare its pre-treatment variables (exposure, activity) with the main population and give a base rate
3. **External claims are hypotheses.** Colleagues' documents, chat messages and search results are the same class of untrusted input: shapes the data can reproduce (timing, magnitude, which region, whether it recovered) are checked and then written; causes and actions the data cannot see (which component, who fixed it) are written as `⚠ to be confirmed manually`. When an external claim is partly overturned, say so clearly
4. **State the estimation stance before estimating.** Point estimate, lower bound or upper bound is a choice that depends on what the number is for (measurement vs risk control); the team's default is in `analysis_priors.stances`, and the report says which was used
5. **Global-replica tables are not summed across regions; entity-level merges key on `(entity, date)`.** Every multi-condition intersection count is bounded by the tightest single condition's global count — a subset larger than its bound is a definition error. Keep a "numerator source / denominator source" ratio column and compare it to a known level; a value outside the range means the merge key or a definition is wrong, not a business insight

## Attribution toolkit (pick what the question needs)

| Module | Answers | Shape |
|---|---|---|
| overview | how big is the gap, which components contribute | group × metric component |
| cross dimension | which source × destination pair is worst | dimension matrix (target group only) |
| within-group gap | where the gap concentrates (population / region) | X vs Y within each group |
| category / content | is distribution reaching high-risk supply | group × content tag |
| counterfactual decomposition | does the gap come from "where traffic went" or "what happened on arrival" | below |
| concentration | a few heavy units or systemic | contribution share of top 1% / 0.1% units |
| stratified standardization | rule out compositional confounders | below |

## Counterfactual decomposition

Identity: `actual − base = (cf − base) + (actual − cf) = structure effect + intensity effect`

- cf = X's traffic re-weighted by Y's rate on the same unit (unit = producer / category / country, by question)
- structure effect → govern selection / routing; intensity effect → govern within-unit mechanisms. Different narratives, different owners; report them apart
- units must carry both X and Y traffic (the overlap is non-random; report its coverage); cf's numerator and denominator keep the same unit

## Confounders (the standard reply to a challenge)

The challenge: "Z drives both selection into X and the metric". Split the structure effect further: `structure = composition (X leans toward some Z tier × that tier is worse anyway) + selection (within the same Z tier, X still picks worse units)`.

Verification ladder, cheap to expensive: ① stratified standardization (Kitagawa) ② same-tier control (measure the unit's inherent level in Y's terms) ③ dose–response / event study (test reverse causation) ④ experiment (gold standard; observational decomposition cannot replace it because traffic redistributes in the counterfactual).

The stratifying variable must be **pre-determined** (fixed before exposure to X) or you over-control; with several Z, walk the team's list in `analysis_priors.confounders` one by one. Even when every confounder holds, the user-side gap is real — "should we act" and "whose mechanism is responsible" are written separately.

## Three confidence tiers (only high enters the document)

| Tier | Condition | Destination |
|---|---|---|
| high | ① criterion written in the BRIEF beforehand and met ② direction consistent across regions / slices ③ main alternative explanations ruled out with data (adversarial review passed) | the document's Conclusions |
| medium | any one condition missing | BRIEF §5 + conversation |
| low | direction only, or a single slice | BRIEF §5 |

No confidence labels in the document; alternatives appear in Conclusions as "❌ Hypothesis N does not hold — criterion …", never as a separate section.

## Adversarial checklist (executed independently by `adversarial-reviewer`)

1. Every core conclusion has ≥1 **concrete** alternative explanation and a design that distinguishes them ("there may be confounding" is not allowed)
2. Definition artifacts: does the numerator or denominator mechanically favor one group
3. Measurement blind spots: is detection or labeling coverage uneven across groups ("cleaner" may be "undetected")
4. Column meaning: a result column's name ≠ its semantics; confirm the mapping in the generating SQL
5. Magnitude: core numbers cross-checked against an independent source; an order of magnitude off means a definition problem
6. Concentration stated: a few heavy units or systemic — it decides the governance narrative
7. Simpson check: does the total gap agree in direction with the within-group gaps
8. Explainability: can each conclusion be said in one plain, complete sentence to a non-technical stakeholder (standard in `report-writing` §3)

Challenges and responses are recorded in BRIEF §5, not in the document. A corrected conclusion is marked "the earlier statement X was wrong because Y", never silently replaced.
