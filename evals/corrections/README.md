# corrections: a ledger of user corrections

The main session logs one case whenever the user overrides or rewrites something — at a gate, while accepting an agent's output, during delivery polish, or in a follow-up. This is a **ledger, not a rulebook**. Rules live in memory / skills / agents / adapter; whether a case becomes a rule is decided by `review.py`'s thresholds and the user.

## What to log (decide `kind` first)

| kind | Criterion | Log? | Can one case become a rule? |
|---|---|---|---|
| `explore` | The analysis direction changed: new hypothesis, dimensions added or removed, different control, scope widened or narrowed, definition re-run. Iteration of the exploration itself, not an agent error | **no** | no |
| `tweak` | A one-off format / wording / layout change with no generalizing language from the user | yes | no; the same `tag` must recur in ≥3 different topics to become a candidate |
| `violation` | A **written** rule was broken (name it: memory slug, skill file, agent file, adapter file) | yes | the rule already exists; this case is evidence that "the rule is there but was not followed" — feed it to graders and regressions |
| `generalize` | The user's words generalize: "from now on", "by default", "always", "never again", "every time" | yes | yes, as a candidate; the user confirms before it is written into memory / skill / adapter |

When unsure, log the weaker kind: an uncertain `generalize` becomes `tweak`; a `violation` that cannot name its rule becomes `tweak`. Several same-kind tweaks in one editing round merge into one case.

## Fields

`id, ts, project, topic, stage, kind, tag, agent_output, user_correction, user_words, existing_rule, rule_candidate, status, promoted_to`

- `stage`: `gate1 | gate2 | data-runner | analysis | adversarial | gate3 | doc-draft | gate4 | publish | followup`
- `tag`: lowercase hyphenated phrase for the behavior that was corrected (e.g. `region-label-in-chart`, `invented-cohort`); reuse existing tags (`review.py --tags`)
- `agent_output` / `user_correction`: ≤200 characters each, excerpt not paraphrase
- `user_words`: the user's own phrase, to re-check the kind later
- `existing_rule`: `memory:<slug>` / `skill:<file>#<section>` / `agent:<name>#<rule>` / `adapter:<file>`; required for `violation`
- `status`: `open | promoted | dismissed`; `promoted_to` names the memory / skill / adapter location

## Follow-up stage

A channel-started `qa-followup` session does not write this directory (its guardrails allow writes only under the projects root). It appends `[to log] followup / kind / tag / summary` to its DM to the owner and marks the QA.md row `[to log]`; the owner logs it from a terminal with `log_correction.py --stage followup`.
