# Privacy and safety

ApplyFlow keeps application tracking data in a local JSON file. It does not
connect to job boards, email accounts, calendars, or employer systems.

## Data stored locally

A record can contain company and role names, a source URL, application and
follow-up dates, its current status, and activity notes. Treat the store as
private career data. Keep it outside public repositories and do not put
passwords, access tokens, government identifiers, demographic answers, salary
documents, or private recruiter messages in notes.

ApplyFlow's default summaries, timelines, recent-activity reports, and daily
plans omit source URLs and activity notes to reduce accidental disclosure. Timeline commands
include note text only after the explicit `--include-notes` option. Company names, role names, dates, and local record IDs
still appear in record-level reports. Weekly reviews are stricter and expose only
aggregate counts for the selected time window.

## Storage safeguards

- The JSON format has an explicit schema version.
- Missing and unknown record fields are rejected.
- Duplicate record IDs are rejected.
- Writes use a temporary file and atomic replacement.
- Active duplicate opportunities are rejected by company and role.
- Local application data patterns are excluded by `.gitignore`.
- Manual notes reject blank text and input longer than 2,000 characters.
- Activity reviews are bounded and hide note text by default.
- Daily plans are read-only, bounded, deduplicated, and never include note text.
- Backups are schema-validated, written atomically, and never overwrite files.
- Restore operations require confirmation and only write to a new destination.
- Weekly reviews expose aggregate counts only and never identify applications.

Atomic replacement helps prevent partial writes. ApplyFlow backups provide local
recovery and SHA-256 change detection, but they are not encryption or proof of
authenticity. Use operating-system disk encryption, restrictive permissions, and
a private backup location.

## Workflow boundaries

Status changes must follow the supported application lifecycle. Terminal
rejected and withdrawn records cannot receive new follow-ups. ApplyFlow only
reports due follow-ups; it never contacts a recruiter or submits an application.
Review every external action yourself.
