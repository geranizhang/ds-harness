<!-- Exemplar: survey / sizing, short form. Fictional marketplace, fictional numbers. Structure per skills/report-writing/references/structure.md.
     Survey reports use degree words and raw start→end pairs instead of ✅/❌ and explained share (patterns 7, 15, 16). -->

# Flash-sale sessions: size, reach and detection timing

# Background

A new flash-sale detector flags listings whose order velocity spikes. Before building on it, the team wants to know how large flash-sale sessions are, whom they reach, and whether the detector fires early enough to matter for ranking.

> Scope: one region, 2026-08-11 to 2026-08-18. The detector's log table has its first partition at 2026-08-11 12:00 and no rows from 2026-08-13 17:00 to 2026-08-18 02:00; only **2026-08-12** is a full calendar day and all daily figures use it.

# TL;DR

1. **Flash-sale sessions are a small slice of sessions with outsized views and conversion, but little revenue.**
   - 0.6% of sessions, 2.4% of page views, 1.1% of checkouts, 0.3% of gross merchandise value
   - Conversion lift is largest for low-activity users: checkout rate vs non-flash sessions +146% (new users), +115% (low), +116% (mid), +77% (high)
2. **The detector fires after views have peaked; it is not earlier than the ranking system.**
   - Page-view peak sits 0–5 minutes *before* detection in both session types
   - Concurrent users are still rising at detection, so detection is late relative to exposure and early relative to crowd build-up
3. **Two session types behave differently after detection.** Scheduled drops plateau and keep converting; viral spikes decay within 20–25 minutes
4. **The detector's data pipeline has a gap** (2026-08-13 17:00 to 2026-08-18 02:00) that the owning team has not explained → the reliability of the log for production use may be insufficient

# Size and efficiency

> Non-flash sessions = all other sessions on the same day. Checkout rate = sessions with a completed checkout / sessions. User activity tiers from the 30-day activity table (new / low / mid / high).

**Flash-sale sessions are rare but concentrated: 0.6% of sessions take 2.4% of page views, and their checkout rate is roughly double the non-flash rate.**

- 1,299 flash-sale sessions on 2026-08-12 — 0.6% of sessions, 2.4% of page views, 1.1% of checkouts
- Gross merchandise value share 0.3%; GMV per session is about a quarter of the non-flash figure → flash traffic brings views and checkouts, not revenue
- Checkout rate lift by activity tier: new +146%, low +115%, mid +116%, high +77%

| metric | flash-sale sessions | non-flash sessions | flash share |
|---|---|---|---|
| sessions | 1,299 | 215,400 | 0.6% |
| page views | 18,900 | 772,000 | 2.4% |
| checkouts | 112 | 10,050 | 1.1% |
| GMV (k) | 3.1 | 1,030 | 0.3% |
| checkout rate | 8.6% | 4.7% | — |

| user tier | flash checkout rate | non-flash checkout rate | lift |
|---|---|---|---|
| new | 5.9% | 2.4% | +146% |
| low | 7.1% | 3.3% | +115% |
| mid | 9.5% | 4.4% | +116% |
| high | 12.4% | 7.0% | +77% |

# Detection timing and traffic shape

> Each session is aligned on its own detection timestamp (t = 0). Page views and concurrent users are averaged per minute across sessions of the same type, from t = −30 to t = +120 minutes. Two types: scheduled drops (seller-announced) and viral spikes (unannounced).

**Detection happens after the page-view peak in both session types; the ranking system has already started to pull back exposure when the detector fires.**

- Scheduled drops: page-view peak 141/min at t = −5 to 0; viral spikes: peak 415/min at t = −5 to 0
- Concurrent users keep rising past detection: scheduled drops to 214 at t = +120 (still rising); viral spikes to 337 at t = +20 to +25
- Detection is late relative to exposure and early relative to crowd size → as a ranking signal it may add little; as a moderation or inventory signal it may be in time

**After detection the two types diverge: scheduled drops settle at about 110 views/min for an hour and keep converting; viral spikes decay from 4× to 177 views/min and most have ended by t = +120.**

| session type | peak page views/min (t) | views/min at t = +60 | concurrent users at t = 0 | concurrent peak (t) | sessions still live at t = +120 |
|---|---|---|---|---|---|
| scheduled drop | 141 (−5 to 0) | 110 | 96 | 214 (+120, still rising) | 23% |
| viral spike | 415 (−5 to 0) | 177 | 188 | 337 (+20 to +25) | 9% |

# Session catalogue

Eight sessions sampled across the window, matched to the real-world trigger.

| trigger | sessions sampled | type | peak concurrent users | checkout rate |
|---|---|---|---|---|
| sneaker restock (announced) | 3 | scheduled drop | 2,240 | 11.2% |
| creator mention (unannounced) | 2 | viral spike | 1,870 | 6.4% |
| price error (unannounced) | 1 | viral spike | 3,310 | 14.0% |
| holiday bundle (announced) | 2 | scheduled drop | 980 | 9.1% |

# Repeat exposure (tbd)

Whether users who hit two or more flash-sale sessions in a week convert differently from single-exposure users. Premise: repeat exposure may either train users to wait for drops (lower everyday conversion) or build habit (higher). Needed before this can be answered:

1. A per-user join of detector sessions to the 30-day activity table across the full week, which the pipeline gap prevents
2. A definition of "everyday conversion" that excludes the flash sessions themselves

# Appendix

## Detector coverage by hour, 2026-08-12

| hour (UTC) | sessions detected | share of day |
|---|---|---|
| 00–06 | 142 | 11% |
| 06–12 | 301 | 23% |
| 12–18 | 519 | 40% |
| 18–24 | 337 | 26% |
