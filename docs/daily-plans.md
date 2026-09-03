# Daily action plans

ApplyFlow can combine the applications that need attention into one bounded,
read-only review:

```bash
applyflow --data ~/private/applications.json plan \
  --as-of 2026-09-03 \
  --horizon-days 7 \
  --inactive-days 14
```

The plan does not change records, send messages, access a calendar, or contact
an employer. It only helps decide what to review manually.

## Priority order

Each active application appears at most once. ApplyFlow uses this order:

1. overdue follow-ups, oldest deadline first;
2. follow-ups due on the selected date;
3. upcoming follow-ups inside the planning horizon, soonest first;
4. stale applications with no follow-up inside the horizon, oldest update first.

A due or upcoming follow-up takes precedence over a stale-record reminder. This
prevents the same application from filling multiple positions in the plan.
Rejected and withdrawn applications are excluded.

## Bounds and exit statuses

The default horizon is 7 days, stale threshold is 14 days, and output limit is
25 actions. Configure them explicitly when needed:

```bash
applyflow --data ~/private/applications.json plan \
  --as-of 2026-09-03 \
  --horizon-days 3 \
  --inactive-days 21 \
  --limit 10 \
  --json
```

The horizon can be zero for a today-only plan. The stale threshold and limit
must be positive. JSON output reports both the displayed count and total
candidate count, plus whether the list was truncated.

The command exits with status 1 when actions need review, 0 when the plan is
empty, and 2 for invalid input or storage.

## Privacy

Plan output includes local application IDs, company names, role names, statuses,
dates, and action reasons. It never includes source URLs or activity-note text.
Treat exported plans as private career data because company and role names can
still be sensitive.
