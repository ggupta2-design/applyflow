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
