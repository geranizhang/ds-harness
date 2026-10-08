<!-- Exemplar: attribution, long form. Fictional marketplace, fictional numbers. Structure per skills/report-writing/references/structure.md.
     Every number in body text appears in a table in the same section. Hypotheses carry criterion → verdict → explained share. -->

# Why cross-region orders are refunded more often than domestic orders

# Background

Refund rate on cross-region orders (buyer and seller in different regions) has sat above the domestic rate for two quarters. The marketplace team wants to know whether this is a supply problem (cross-region sellers are worse), a friction problem (buyers expect something different when buying across a border), or a mix problem (cross-region orders land in categories that are refunded more anyway) — because each points at a different owner.

> Scope: orders placed 2026-07-01 to 2026-07-31, two buyer regions (NA, EU), consumer marketplace only. Refund rate = refunded orders / delivered orders, summed then divided. Cross-region = seller region ≠ buyer region.

# Conclusions

- **Hypothesis 1 — cross-region sellers supply worse goods: ❌ does not hold.** Criterion: holding category fixed, compare the seller's refund rate at home with the buyer region's domestic rate. Cross-region sellers are refunded *less* at home than domestic sellers are (apparel 8.1% vs 9.8%); the supply term explains −12% of the gap.
- **Hypothesis 2 — cross-border friction (shipping time, sizing, expectations) raises refunds: partial.** Criterion: holding category and seller fixed, compare the same seller's refund rate on cross-region vs home orders. The friction term explains 28% of the gap, concentrated in apparel.
- **Hypothesis 3 — cross-region orders are concentrated in high-refund categories: ✅ holds, explains 71% of the gap.** Apparel is 48% of cross-region orders but 22% of domestic ones, and apparel is refunded at 9.8% against 2.1% for electronics. Removing apparel and footwear, the cross-region refund rate is *below* domestic.
- **Hypothesis 4 — price tier: ❌ does not hold.** Criterion: within each price band, compare cross-region with domestic. The ordering is the same in every band; the price-band composition term explains 4%.
- Both regions show the same picture; NA's gap is larger (+52% relative) than EU's (+38%) because NA's cross-region apparel share is higher.

# Refund rate by buyer region

> Metrics: refund rate as defined above; relative gap = (cross-region rate − domestic rate) / domestic rate. Both regions, July 2026.

**Cross-region orders are refunded 45% more often than domestic orders overall; the gap exists in both regions and is larger in NA.**

- Domestic 4.2%, cross-region 6.1%, relative gap +45%
- NA: 4.0% → 6.1% (+52%); EU: 4.5% → 6.2% (+38%)
- Cross-region orders are 19% of delivered orders but 25% of refunds

| buyer region | domestic refund rate | cross-region refund rate | relative gap | cross-region share of orders | cross-region share of refunds |
|---|---|---|---|---|---|
| NA | 4.0% | 6.1% | +52% | 21% | 28% |
| EU | 4.5% | 6.2% | +38% | 16% | 21% |
| ALL | 4.2% | 6.1% | +45% | 19% | 25% |

# Category mix

> Categories: the five top-level marketplace categories; "other" merges the long tail. Share = category's share of delivered orders on that side. Rate = refund rate within the category.

**Cross-region demand is concentrated in apparel and footwear, the two categories with the highest refund rates; this concentration alone explains 71% of the gap.**

- Apparel is 48% of cross-region orders vs 22% of domestic; footwear 14% vs 9%
- Apparel refund rate 9.8%, footwear 7.4%, electronics 2.1%, home 3.0%
- Within apparel, cross-region orders are refunded *less* than domestic (9.1% vs 9.8%); the same holds in footwear and home

| category | domestic share | cross-region share | domestic refund rate | cross-region refund rate |
|---|---|---|---|---|
| apparel | 22% | 48% | 9.8% | 9.1% |
| footwear | 9% | 14% | 7.4% | 7.0% |
| electronics | 31% | 15% | 2.1% | 2.6% |
| home | 24% | 13% | 3.0% | 2.8% |
| other | 14% | 10% | 2.4% | 2.5% |

> **Decomposition.** For category i, with s = share of orders and r = refund rate, subscripts 1 = cross-region, 0 = domestic:
>
> composition effect = (s_i1 − s_i0) × (r_i0 + r_i1) / 2 — "how much more of the mix went to this category" × "how refund-prone the category is"
>
> rate effect = (s_i0 + s_i1) / 2 × (r_i1 − r_i0) — "how big the category is" × "how much more cross-region buyers refund it than domestic buyers"
>
> The two sum exactly to the overall gap. Composition is a routing question; rate is a within-category experience question.

| category | composition effect (pp) | rate effect (pp) | share of total gap |
|---|---|---|---|
| apparel | +2.46 | −0.25 | +116% |
| footwear | +0.36 | −0.05 | +16% |
| electronics | −0.38 | +0.12 | −14% |
| home | −0.32 | −0.04 | −19% |
| other | −0.10 | +0.01 | −5% |
| **total** | **+2.02** | **−0.21** | composition 71% of gap after netting; rate −9% |

**Removing apparel and footwear, cross-region orders are refunded less often than domestic (2.4% vs 2.5%).**

| scope | domestic refund rate | cross-region refund rate | relative gap |
|---|---|---|---|
| all categories | 4.2% | 6.1% | +45% |
| excluding apparel and footwear | 2.5% | 2.4% | −4% |

# Supply quality vs buyer friction

> Three rates per category and seller region: R_home = the cross-region seller's refund rate on orders from buyers in the seller's own region; R_dom = the buyer region's domestic refund rate; R_cross = the cross-region rate. Supply term = (R_home − R_dom) × s_1; friction term = (R_cross − R_home) × s_1. Both are expressed as a share of the total gap.

**Cross-region sellers are refunded less at home than domestic sellers are in the buyer's region, so supply quality does not explain the gap; the residual is buyer-side friction, concentrated in apparel.**

- Apparel: sellers' home refund rate 8.1% vs buyer-region domestic 9.8% — the goods are not worse
- Friction term is +28% of the gap overall, +24% of it inside apparel (sizing and return-shipping reasons dominate the refund-reason field)
- Supply term is −12% of the gap: it works against the gap, not for it

| category | R_home (seller at home) | R_dom (buyer region domestic) | R_cross | supply term | friction term |
|---|---|---|---|---|---|
| apparel | 8.1% | 9.8% | 9.1% | −9% | +24% |
| footwear | 6.6% | 7.4% | 7.0% | −2% | +3% |
| electronics | 2.0% | 2.1% | 2.6% | −0% | +2% |
| home | 2.9% | 3.0% | 2.8% | −0% | −1% |
| other | 2.4% | 2.4% | 2.5% | 0% | +0% |
| **total** | | | | **−12%** | **+28%** |

# Price tier

> Price bands on order value in buyer currency, converted at the monthly average rate; four bands with roughly equal order counts on the domestic side.

**Within every price band, cross-region orders are refunded more than domestic ones, and the band mix differs little between the two sides; price tier explains 4% of the gap.**

| price band | domestic share | cross-region share | domestic refund rate | cross-region refund rate |
|---|---|---|---|---|
| < 20 | 26% | 24% | 3.1% | 4.6% |
| 20–50 | 25% | 27% | 4.0% | 5.9% |
| 50–120 | 25% | 26% | 4.7% | 6.8% |
| > 120 | 24% | 23% | 5.0% | 7.1% |

# Case review

Top ten refunded cross-region apparel listings in each region, by refund count, with the recorded refund reason. Sizing mismatch and "item differs from photos" account for most of the volume; damaged-in-transit is rare.

| region | listings reviewed | sizing mismatch | differs from photos | damaged in transit | other |
|---|---|---|---|---|---|
| NA | 10 | 6 | 3 | 0 | 1 |
| EU | 10 | 5 | 3 | 1 | 1 |

# Appendix

## Refund rate by seller region × buyer region

**The seller region with the largest cross-region apparel volume into NA is EU; its apparel refund rate into NA (9.3%) is close to its home rate (8.4%).**

| seller region → buyer region | apparel orders share | apparel refund rate |
|---|---|---|
| EU → NA | 61% | 9.3% |
| APAC → NA | 39% | 8.8% |
| NA → EU | 55% | 8.9% |
| APAC → EU | 45% | 9.4% |
| EU → EU (home) | — | 8.4% |
| NA → NA (home) | — | 7.9% |

## Daily refund rate, July 2026

| week | domestic | cross-region |
|---|---|---|
| 07-01 to 07-07 | 4.1% | 6.0% |
| 07-08 to 07-14 | 4.3% | 6.2% |
| 07-15 to 07-21 | 4.2% | 6.1% |
| 07-22 to 07-31 | 4.2% | 6.0% |
