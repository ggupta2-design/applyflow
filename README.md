# ApplyFlow

ApplyFlow is a local-first command-line tool for tracking job applications and
follow-ups without sharing career data with a third-party service.

The first release focuses on a safe application workflow:

- record saved and submitted opportunities;
- move applications through explicit, validated stages;
- schedule and review follow-ups;
- keep an append-only activity history;
- produce readable or JSON summaries for personal automation.

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
```

ApplyFlow supports saved, applied, interviewing, offer, rejected, and withdrawn
stages. Invalid stage jumps are rejected, terminal outcomes clear follow-ups,
and every accepted change is recorded in the local activity history.

The `due` command returns status 1 when follow-ups need attention. The `pipeline` command summarizes stage counts and interview or offer conversion, while `stale` flags active records that have not changed recently. JSON reports are
available with `--json` and omit source URLs and activity notes.

See the [usage guide](docs/usage.md) and
[privacy and safety guide](docs/privacy-and-safety.md), and [analytics guide](docs/analytics.md) for details.
