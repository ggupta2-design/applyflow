# Pipeline analytics and stale reviews

ApplyFlow can summarize a private local application store without changing any
records or connecting to an external service.

## Pipeline summary

```bash
applyflow --data ~/private/applications.json pipeline
applyflow --data ~/private/applications.json pipeline --json
```

The report includes current stage counts, active and terminal totals, submitted
applications, and the percentage of submitted applications that reached an
interview or offer. A record counts as reaching a milestone when that stage is
present in its append-only history, even if the current outcome is rejected or
withdrawn.

Rates describe the records in the selected local store. They are not predictions
of future hiring outcomes, and a small pipeline can produce unstable
percentages.

## Stale application review

```bash
applyflow --data ~/private/applications.json stale \
  --as-of 2026-09-01 \
  --inactive-days 14
```

A stale record is active and has not been updated for at least the selected
number of days. Rejected and withdrawn records are excluded. Results are ordered
from the longest-inactive record to the newest.

The command exits with status 1 when records need review, 0 when none are stale,
and 2 for invalid input or storage. It never changes a status, schedules a
follow-up, sends a message, or contacts an employer.

## Privacy boundaries

Pipeline reports contain aggregate counts and rates only. Stale reports include
the local record ID, company, role, current status, dates, and inactive-day
count. Both report types omit source URLs and activity notes. Company and role
names remain personal career data, so review JSON before sharing it.
