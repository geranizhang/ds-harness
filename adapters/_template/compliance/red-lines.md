# Compliance red lines (template)

**The single authoritative statement of what is forbidden on this platform.** Agents link here; they do not restate it. If your platform has no compliance constraints, say so in one line and leave `compliance.guard.submit_patterns` empty.

## Forbidden

1. …
2. …

## Mechanically enforced

Which of the above are checked by `platform/checks.py` (and therefore by the guard hook at submission time), and which rely on the agent reading this file.

## What this implies for grain

Row-level thresholds or aggregation requirements that set the finest grain a query can return. State them plainly so `data-runner` can write "not obtained" instead of looking for a workaround.
