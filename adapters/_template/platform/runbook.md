# Platform runbook (template)

One section per region/engine. Everything the `data-runner` agent needs to go from a SQL file to rows on disk without asking anyone. Keep dated evidence (`YYYY-MM-DD: observed …`) separate from rules.

## Routing

| Region | Engine / gateway | Compliance constraints | Who may run it |
|---|---|---|---|
| REGION_A | | none / describe | |
| REGION_B | | | |

## Per-region connection

| Region | CLI flag | Queue / resource pool | Login | Session lifetime |
|---|---|---|---|---|

## Submit → poll → fetch

- Sync path (probes, smoke, small results): command, timeout, how to read the JSON
- Async path (large / long): create file → run → poll (interval, terminal states — **whitelist them**, never "break on non-running") → fetch
- Fetch caps: rows / bytes per fetch, how truncation manifests (silent? unordered?), the field that carries the true row count
- Result retention: how long results stay fetchable

## Known failure signatures

| Symptom | Likely cause | First thing to check |
|---|---|---|
| job fails within seconds, no diagnostics | wrong queue for this region / unsupported function | queue list; grep SQL for … |
| succeeded but far fewer rows than expected, small result set | engine optimizer bug | … |

## Compliance red lines (if any)

The single authoritative statement of what is forbidden on this platform. Agents link here; they do not restate it.
