# Metric dictionary (template)

Every metric carries the five items the core workflow requires: **meaning, source field, numerator/denominator, aggregation, approximation error**.

## <metric name>

**Rules**
- Source: `db.table.column`
- Numerator / denominator:
- Aggregation: sum then divide (never average ratios across rows)
- Approximation: UV is not additive across days; summing gives person-days

**Evidence** (dated; a result of one analysis, not a rule — check the time window before reuse)
- YYYY-MM-DD: …
