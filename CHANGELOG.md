# Changelog

## 0.6.0 — 2026-09-05

- Added inclusive seven-day application progress reviews.
- Added deduplicated submission, interview, offer, and closure metrics.
- Added weekly activity and active-pipeline counts.
- Added overdue and next-seven-day follow-up workload totals.
- Added configurable weekly submission goals and progress tracking.
- Added count-only readable and JSON reports with no application identifiers.
- Added the week CLI command and positive-target validation.
- Added weekly review tests, workflow documentation, and privacy guidance.

## 0.5.0 — 2026-09-04

- Added schema-validated, atomic backups that never overwrite files.
- Added SHA-256 backup digests and optional expected-checksum verification.
- Added constant-time checksum comparison and strict digest validation.
- Added explicitly confirmed restores that only target new files.
- Added value-free backup reports that omit application data and parent paths.
- Added backup, verify-backup, and restore CLI commands.
- Added backup integrity, recovery, CLI, and privacy tests.
- Added recovery workflow documentation and security boundaries.

## 0.4.0 — 2026-09-03

- Added read-only daily action plans for active applications.
- Prioritized overdue, due-today, upcoming, and stale-record reviews.
- Deduplicated actions so follow-up work takes precedence over stale reminders.
- Added configurable planning horizons, stale thresholds, and output limits.
- Added deterministic ordering and explicit truncation metadata.
- Added privacy-safe readable and JSON reports.
- Added a plan CLI command with automation-friendly exit statuses.
- Added planning tests, workflow documentation, and privacy guidance.

## 0.3.0 — 2026-09-02

- Added validated manual notes without implicit status changes.
- Added stable chronological timelines and newest-first cross-application activity.
- Added inclusive date filtering and explicit positive result limits.
- Added readable and JSON activity reports that hide note text by default.
- Added explicit opt-in note disclosure for private review destinations.
- Added note, history, and activity CLI commands.
- Added activity tests, usage documentation, and privacy guidance.

## 0.2.0 — 2026-09-01

- Added read-only application stage and pipeline totals.
- Added history-aware interview and offer conversion rates.
- Added stale active-application detection with configurable thresholds.
- Added deterministic oldest-first stale review ordering.
- Added privacy-aware readable and JSON analytics reports.
- Added pipeline and stale-review CLI commands with automation-friendly statuses.
- Added analytics tests, workflow documentation, and metric privacy guidance.

## 0.1.0 — 2026-08-31

- Added validated local job application records.
- Added strict, versioned JSON loading and atomic writes.
- Added active-opportunity duplicate prevention.
- Added guarded saved, applied, interviewing, offer, rejected, and withdrawn transitions.
- Added append-only status and follow-up activity history.
- Added follow-up scheduling and due-date reviews.
- Added privacy-aware readable and JSON summaries.
- Added the local-first command-line interface.
- Added Python 3.10–3.13 tests, workflow documentation, and privacy guidance.
