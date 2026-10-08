# Table handbook (template)

## Scope index — check before summing across regions

| Table | Scope | Available in | One-line purpose |
|---|---|---|---|
| `db.table_a` | partitioned-by-region | REGION_A, REGION_B | |
| `db.dim_b` | **global replica** (summing across regions = N× overcount) | all | |
| `db.table_c` | merged single source | REGION_A only | |
| `db.table_d` | unverified — do a one-cell cross-region comparison before summing | | |

## Entry format

```
## db.table_name
Owner · TTL · regions
- Grain: one row = …
- Partitions: date (yyyyMMdd) + …
- Key columns: … (units!)
- Gotchas: (dated evidence goes here, with the date)
- Join keys: …
```
