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
