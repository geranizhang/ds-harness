"""Adapter regression cases, loaded by <harness>/evals/run_validators.py.

`cases(ctx)` returns callables `case(tmp)`; ctx exposes run / expect / w / HDR / V_SQL / V_RAW / V_DOC / V_XLSX.
Add one bad SQL that must fail your dialect checks and one good SQL that must pass.
"""


def cases(ctx):
    return []
