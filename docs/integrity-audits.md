# Application integrity audits

ApplyFlow can inspect the semantic relationships inside a valid local store
without changing it:

```bash
applyflow --data ~/private/applications.json audit --as-of 2026-09-06
applyflow --data ~/private/applications.json audit --as-of 2026-09-06 --json
```

The explicit review date makes future-date checks reproducible in scripts and
tests.

## Checks

The audit reports stable finding codes for:

- records with no activity history;
- a current status that does not match the latest history entry;
- stage changes that skip the supported application lifecycle;
- updates that predate creation;
- timestamps without timezone information;
- activity that is out of order or outside the record's time window;
- record or application dates later than the selected review date;
- submitted records with no application date;
- terminal records that still have a follow-up;
- duplicate active opportunities with the same case-insensitive company and
  role.

Errors indicate internal contradictions. Warnings identify plausible data that
deserves manual review, such as future dates or duplicate active opportunities.

## Automation statuses

The command exits with:

- 0 when no findings exist;
- 1 when at least one warning or error needs review;
- 2 when arguments or storage are invalid.

A finding never triggers an automatic repair. Make a verified backup before
editing a store, correct the underlying record deliberately, and run the audit
again.

## Privacy boundary

Text and JSON output contain only the review date, number of records checked,
severity totals, and aggregate counts by finding code. They never include
application IDs, company names, roles, URLs, dates from individual records, or
activity notes. The local store is read in memory and is not uploaded.
