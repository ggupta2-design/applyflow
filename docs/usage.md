# Using ApplyFlow

Install in a virtual environment:

```bash
python -m pip install -e .
```

Use `--data` to choose a private local store. If omitted, ApplyFlow uses
`applyflow.json` in the current directory.

## Record an opportunity

```bash
applyflow --data ~/private/applications.json add \
  --company "Example Company" \
  --role "Data Analyst" \
  --url "https://example.com/jobs/123"
```

Record a submitted application and its next review date:

```bash
applyflow --data ~/private/applications.json add \
  --company "Example Company" \
  --role "Operations Analyst Intern" \
  --status applied \
  --applied-on 2026-08-31 \
  --follow-up-on 2026-09-08
```

## Review and update the pipeline

```bash
applyflow --data ~/private/applications.json list
applyflow --data ~/private/applications.json list --status applied --json
applyflow --data ~/private/applications.json move APPLICATION_ID interviewing \
  --note "Phone screen scheduled"
```

Invalid jumps, such as moving directly from saved to offer, are rejected.

## Schedule follow-ups

```bash
applyflow --data ~/private/applications.json schedule APPLICATION_ID \
  --on 2026-09-10
applyflow --data ~/private/applications.json due --as-of 2026-09-10 --json
applyflow --data ~/private/applications.json schedule APPLICATION_ID --clear
```

The `due` command exits with status 1 when follow-ups need attention and 0
when none are due. Invalid input or storage returns status 2. The command only
reports reminders; it does not send messages or access a calendar.

See [privacy-and-safety.md](privacy-and-safety.md) before storing real
application information.



## Review pipeline progress

Summarize current stages and milestone conversion without changing records:

```bash
applyflow --data ~/private/applications.json pipeline
applyflow --data ~/private/applications.json pipeline --json
```

Find active records that have not changed recently:

```bash
applyflow --data ~/private/applications.json stale \
  --as-of 2026-09-01 \
  --inactive-days 14 \
  --json
```

The stale command returns status 1 when records need manual review and 0 when
none meet the threshold. Rejected and withdrawn applications are excluded.
Neither command exposes source URLs or activity notes. See
[analytics.md](analytics.md) for metric definitions and privacy boundaries.


## Record and review activity

Append a private note without moving the application to another stage:

```bash
applyflow --data ~/private/applications.json note APPLICATION_ID \
  --text "Portfolio requested"
```

Review one application's full timeline or a bounded cross-application feed:

```bash
applyflow --data ~/private/applications.json history APPLICATION_ID
applyflow --data ~/private/applications.json activity \
  --since 2026-09-01 \
  --limit 25 \
  --json
```

Activity notes are omitted from text and JSON reports by default. Use
`--include-notes` only for a private destination where the note content is
needed. See [activity.md](activity.md) for ordering, limits, and privacy
guidance.


## Build a daily action plan

Combine overdue, due, upcoming, and stale-record reviews without changing data:

```bash
applyflow --data ~/private/applications.json plan \
  --as-of 2026-09-03 \
  --horizon-days 7 \
  --inactive-days 14 \
  --limit 25
```

Add `--json` for automation. The command returns status 1 when the plan has
actions, 0 when it is empty, and 2 for invalid input. Each application appears
at most once, follow-up actions take priority over staleness, and source URLs
and notes are always omitted. See [daily-plans.md](daily-plans.md) for the full
priority rules and safety boundaries.


## Back up and recover local data

Create a validated snapshot at a new path:

```bash
applyflow --data ~/private/applications.json backup \
  ~/private/backups/applyflow.json \
  --json
```

Verify its schema and recorded checksum without changing it:

```bash
applyflow verify-backup ~/private/backups/applyflow.json \
  --sha256 EXPECTED_SHA256
```

Restore only to a new output path with explicit confirmation:

```bash
applyflow restore ~/private/backups/applyflow.json \
  --output ~/private/recovered/applications.json \
  --confirm
```

Backup and restore operations refuse to overwrite files. Reports contain only
value-free metadata and omit parent directories. See
[backups.md](backups.md) for the complete recovery workflow and security
boundaries.
