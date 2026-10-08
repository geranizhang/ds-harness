# Workspace conventions (project layout / provenance / versions)

## Directory skeleton

One project = one group of related questions; topics hang under it:

```
<projects_root>/<project>/              # e.g. ~/work/projects/traffic-quality
  PROJECT.md                            # index: topics, status, links to published documents
  references/                           # project-level shared knowledge (agreed definitions, common tables, context)
  topics/
    YYYYMM_<topic-slug>/
      BRIEF.md                          # background + analysis brief (analysis-brief output)
      references/                       # topic-specific material
      sql/                              # working queries
      raw/                              # retrieved source data (kept in full, see below)
      work/                             # scripts + intermediate data
      deliverables/                     # final xlsx / html / md
      versions.csv                      # deliverable version ledger
      LOG.md                            # run log
  QA.md                                 # follow-up ledger (when a Q&A channel is bound)
```

Knowledge has three layers, nearest first, promoted upward: adapter references (whole team) → project references (group consensus) → topic references (this topic only). A definition used by a second topic moves up one layer.

## New topic

1. List existing projects and their topics (each `PROJECT.md`); ask "new project, or a follow-on under X?"
2. On confirmation create `topics/YYYYMM_<slug>/` + BRIEF.md and register one line in PROJECT.md
3. Nothing runs before the placement is confirmed

## Provenance (the most important rule)

Every deliverable traces back to its origin: `deliverable ← work/script ← raw/data ← sql/query`.

- Raw file naming: `raw/YYYYMMDD_<content>_<REGION>.csv` (pattern in the adapter), beside it the **same-name `.sql`** (the version actually executed, definitions in its header block) and the **same-name `.meta.json`** (`{"rowCount", "fetched", "taskId", "region"}`, proof of no truncation). `sql/` holds working drafts; the `.sql` next to raw is the executed copy and is what `validate_raw.py` checks
- Script headers state input and output files
- Every run appends a line to LOG.md: `date | which hypothesis (BRIEF #) | command or script | output file`

## Raw data: keep everything, reuse first

- Raw files are **all kept and committed** (not git-ignored) — source data is reusable across topics with different processing and saves re-runs
- **Look for reusable raw before running**: scan `topics/*/raw/` by name; on a hit, read the sibling SQL to confirm the definition matches; log the source path in this topic's LOG.md
- A near-but-different definition is re-run, not reused

## Deliverable versions

- Same name, different version: `<name>_v1.xlsx` → `_v2.xlsx`; old versions are never deleted or overwritten
- Semantics: **changed definition / data scope / columns = major** (v1→v2; the numbers mean something else, downstream documents must switch); **changed layout / header wording = minor** (v2→v2.1; numbers unchanged)
- An xlsx deliverable lands with a same-name CSV; **diffs between versions are read on the CSV**

### versions.csv (one per topic)

Columns: `deliverable, version, date, change, definition_changed, script, source_data, synced_to_documents`

- "change" is a complete sentence ("report-rate denominator changed from UV to PV"), not field abbreviations
- "definition_changed" = yes → the previous version's numbers are retired; **check "synced_to_documents" and update those documents**

## git

- One project, one repository (`git init` at the project root)
- Everything is committed, including raw / xlsx / html; "going back in time" is git's job, "seeing what changed" is the ledger's and the CSV diff's
- Commit at: ① topic creation ② every raw batch landed ③ every deliverable version (register in versions.csv first)
- Message format: `[<topic-slug>] <action>`; a deliverable version reads `[topic] report rate by region v2: denominator UV→PV`
