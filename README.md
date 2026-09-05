# ApplyFlow

ApplyFlow is a local-first command-line tool for tracking job applications and
follow-ups without sharing career data with a third-party service.

The first release focuses on a safe application workflow:

- record saved and submitted opportunities;
- move applications through explicit, validated stages;
- schedule and review follow-ups;
- build a prioritized daily action plan from follow-ups and stale records;
- review count-only weekly progress against a submission goal;
- keep an append-only activity history and private manual notes;
- review one timeline or bounded recent activity with notes hidden by default;
- produce readable or JSON summaries for personal automation;
- create, verify, and safely restore local backups without overwriting files.

## Privacy and safety

Application records stay in a local JSON file chosen by the user. ApplyFlow does
not submit applications, scrape job sites, send messages, or request account
credentials. Writes are atomic, malformed data is rejected, and existing files
are never silently discarded.

ApplyFlow is being built as part of an eight-week automation project challenge.


## Quick start

```bash
python -m pip install -e .

applyflow --data ~/private/applications.json add \
  --company "Example Company" \
  --role "Data Analyst" \
  --status applied \
  --follow-up-on 2026-09-08

applyflow --data ~/private/applications.json list
applyflow --data ~/private/applications.json due --as-of 2026-09-08
applyflow --data ~/private/applications.json pipeline
applyflow --data ~/private/applications.json stale --inactive-days 14
applyflow --data ~/private/applications.json note APPLICATION_ID --text "Portfolio requested"
applyflow --data ~/private/applications.json history APPLICATION_ID
applyflow --data ~/private/applications.json activity --since 2026-09-01 --limit 25
applyflow --data ~/private/applications.json plan --as-of 2026-09-03 --json
applyflow --data ~/private/applications.json week --ending 2026-09-05 --json
applyflow --data ~/private/applications.json backup ~/private/backups/applyflow.json
applyflow verify-backup ~/private/backups/applyflow.json
```

ApplyFlow supports saved, applied, interviewing, offer, rejected, and withdrawn
stages. Invalid stage jumps are rejected, terminal outcomes clear follow-ups,
and every accepted change is recorded in the local activity history.

The `due` command returns status 1 when follow-ups need attention. The `plan`
command builds a bounded, deduplicated daily list of overdue, upcoming, and
stale-record reviews. The `pipeline` command summarizes stage counts and interview or offer conversion, while `stale` flags active records that have not changed recently. JSON reports are
available with `--json` and omit source URLs and activity notes. The `history`
and `activity` commands reveal notes only with an explicit `--include-notes`.

See the [usage guide](docs/usage.md) and
[privacy and safety guide](docs/privacy-and-safety.md), [analytics guide](docs/analytics.md), and [activity guide](docs/activity.md), and [daily planning guide](docs/daily-plans.md), and [backup guide](docs/backups.md), and [weekly review guide](docs/weekly-reviews.md) for details.
