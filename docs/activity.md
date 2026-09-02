# Application activity and private notes

ApplyFlow keeps an append-only activity history inside each local application
record. Status changes and follow-up scheduling already create activity entries.
Version 0.3 also supports deliberate manual notes and read-only timeline reviews.

## Record a note

```bash
applyflow --data ~/private/applications.json note APPLICATION_ID \
  --text "Portfolio requested; review before Friday"
```

A note updates the record's activity timestamp but does not change its status,
follow-up date, or contact anyone. Notes must contain text and are limited to
2,000 characters so accidental file-sized input is rejected.

## Review one timeline

```bash
applyflow --data ~/private/applications.json history APPLICATION_ID
applyflow --data ~/private/applications.json history APPLICATION_ID --json
```

Notes are hidden by default in both formats. Add `--include-notes` only when the
output destination is private and intentional:

```bash
applyflow --data ~/private/applications.json history APPLICATION_ID \
  --include-notes
```

## Review recent activity

```bash
applyflow --data ~/private/applications.json activity \
  --since 2026-09-01 \
  --limit 25 \
  --json
```

The inclusive `--since` filter starts at midnight UTC on the selected date.
The default limit is 50 and every limit must be positive. Results are ordered
newest first with deterministic tie-breaking.

Recent-activity reports include local record IDs, company names, role names,
statuses, and timestamps. They omit source URLs. Note text remains absent unless
`--include-notes` is supplied.

## Privacy boundaries

Notes can contain sensitive career context. Avoid credentials, government
identifiers, demographic answers, compensation documents, or private contact
details. Keep the JSON store and any report created with `--include-notes` out
of public repositories and shared automation logs.

ApplyFlow never synchronizes, emails, submits, or publishes activity. All
commands in this guide operate only on the local store selected with `--data`.
