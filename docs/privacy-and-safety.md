# Privacy and safety

ApplyFlow keeps application tracking data in a local JSON file. It does not
connect to job boards, email accounts, calendars, or employer systems.

## Data stored locally

A record can contain company and role names, a source URL, application and
follow-up dates, its current status, and activity notes. Treat the store as
private career data. Keep it outside public repositories and do not put
passwords, access tokens, government identifiers, demographic answers, salary
documents, or private recruiter messages in notes.

ApplyFlow's default summaries omit source URLs and activity notes to reduce
accidental disclosure. Company names, role names, dates, and local record IDs
still appear in reports.

## Storage safeguards

- The JSON format has an explicit schema version.
- Missing and unknown record fields are rejected.
- Duplicate record IDs are rejected.
- Writes use a temporary file and atomic replacement.
- Active duplicate opportunities are rejected by company and role.
- Local application data patterns are excluded by `.gitignore`.

Atomic replacement helps prevent partial writes but is not backup or encryption.
Use operating-system disk encryption and a private backup if needed.

## Workflow boundaries

Status changes must follow the supported application lifecycle. Terminal
rejected and withdrawn records cannot receive new follow-ups. ApplyFlow only
reports due follow-ups; it never contacts a recruiter or submits an application.
Review every external action yourself.
