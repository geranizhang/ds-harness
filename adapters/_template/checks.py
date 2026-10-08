"""Adapter-specific SQL dialect checks. Loaded by skills/analysis-workflow/scripts/validate_sql.py.

Return (errors, warnings) as lists of strings. Errors block submission; warnings are advisory.
Core checks (header block, sampling, in-SQL binning) run regardless; put only *platform* rules here:
unsupported functions, gateway quirks, compliance-mandated column shapes, row-level thresholds.
"""


def sql_checks(sql: str, region: str):
    errors, warnings = [], []
    # Example:
    # if region == "REGION_A" and "max_pt(" in sql.lower():
    #     errors.append("REGION_A engine does not support max_pt(); use an explicit partition date")
    return errors, warnings
