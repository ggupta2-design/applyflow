# Weekly progress reviews

ApplyFlow can summarize one inclusive seven-day window without listing
individual applications:

```bash
applyflow --data ~/private/applications.json week \
  --ending 2026-09-05 \
  --target-submissions 5
```

The selected ending date and previous six calendar days form the review window.

## Metrics

The review reports:

- applications created during the week;
- applications submitted during the week;
- applications that reached interviewing or offer during the week;
- applications closed as rejected or withdrawn during the week;
- total activity entries recorded during the week;
- current active and total pipeline sizes;
- active follow-ups overdue as of the ending date;
- active follow-ups due during the next seven days;
- progress toward a positive weekly submission target.

Each application counts at most once in each milestone metric, even if repeated
activity entries reached the same stage. Window boundaries are inclusive.

## Automation output

Use JSON for scripts:

```bash
applyflow --data ~/private/applications.json week \
  --ending 2026-09-05 \
  --target-submissions 4 \
  --json
```

A valid report returns status 0. Invalid input or storage returns status 2.
ApplyFlow does not automatically submit applications, change records, schedule
calendar events, or contact employers.

## Privacy

Weekly reports are count-only. They never include application IDs, company or
role names, source URLs, dates from individual records, or activity notes.
The aggregate counts can still reveal personal job-search patterns, so keep
saved reports private.
