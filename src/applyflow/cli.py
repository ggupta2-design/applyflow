"""ApplyFlow command-line interface."""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Sequence

from .activity import recent_activity
from .analytics import find_stale_applications, summarize_pipeline
from .models import ApplicationError, ApplicationStatus
from .report import (
    format_applications,
    format_due_follow_ups,
    format_pipeline,
    format_recent_activity,
    format_stale_applications,
    format_timeline,
)
from .service import (
    add_application_note,
    create_application,
    due_follow_ups,
    get_application,
    list_applications,
    schedule_follow_up,
    transition_application,
)
from .storage import ApplicationStore, StorageError


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected an ISO date: YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="applyflow",
        description="Track job applications and follow-ups locally",
    )
    parser.add_argument("--version", action="version", version="applyflow 0.3.0")
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("applyflow.json"),
        help="local JSON store path",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="record a saved or submitted opportunity")
    add.add_argument("--company", required=True)
    add.add_argument("--role", required=True)
    add.add_argument(
        "--status",
        choices=[ApplicationStatus.SAVED.value, ApplicationStatus.APPLIED.value],
        default=ApplicationStatus.SAVED.value,
    )
    add.add_argument("--url")
    add.add_argument("--applied-on", type=_date)
    add.add_argument("--follow-up-on", type=_date)
    add.add_argument("--json", action="store_true", dest="as_json")

    listing = commands.add_parser("list", help="list application summaries")
    listing.add_argument("--status", choices=[item.value for item in ApplicationStatus])
    listing.add_argument("--company")
    listing.add_argument("--json", action="store_true", dest="as_json")

    move = commands.add_parser("move", help="move an application to a valid stage")
    move.add_argument("application_id")
    move.add_argument("status", choices=[item.value for item in ApplicationStatus])
    move.add_argument("--note")
    move.add_argument("--json", action="store_true", dest="as_json")

    schedule = commands.add_parser("schedule", help="set or clear a follow-up date")
    schedule.add_argument("application_id")
    target = schedule.add_mutually_exclusive_group(required=True)
    target.add_argument("--on", type=_date)
    target.add_argument("--clear", action="store_true")
    schedule.add_argument("--json", action="store_true", dest="as_json")

    note = commands.add_parser("note", help="append a private note without changing status")
    note.add_argument("application_id")
    note.add_argument("--text", required=True)
    note.add_argument("--json", action="store_true", dest="as_json")

    history = commands.add_parser("history", help="review one application timeline")
    history.add_argument("application_id")
    history.add_argument("--include-notes", action="store_true")
    history.add_argument("--json", action="store_true", dest="as_json")

    activity = commands.add_parser(
        "activity",
        help="review recent activity across applications",
    )
    activity.add_argument("--since", type=_date)
    activity.add_argument("--limit", type=int, default=50)
    activity.add_argument("--include-notes", action="store_true")
    activity.add_argument("--json", action="store_true", dest="as_json")

    pipeline = commands.add_parser(
        "pipeline",
        help="summarize stages and conversion without changing records",
    )
    pipeline.add_argument("--json", action="store_true", dest="as_json")

    stale = commands.add_parser(
        "stale",
        help="review active applications with no recent update",
    )
    stale.add_argument("--as-of", type=_date, default=date.today())
    stale.add_argument("--inactive-days", type=int, default=14)
    stale.add_argument("--json", action="store_true", dest="as_json")

    due = commands.add_parser("due", help="list follow-ups due by a date")
    due.add_argument("--as-of", type=_date, default=date.today())
    due.add_argument("--json", action="store_true", dest="as_json")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = ApplicationStore(args.data)
    try:
        if args.command == "add":
            application = create_application(
                store,
                company=args.company,
                role=args.role,
                status=ApplicationStatus(args.status),
                source_url=args.url,
                applied_on=args.applied_on,
                follow_up_on=args.follow_up_on,
            )
            print(format_applications((application,), as_json=args.as_json, heading="Added"))
            return 0
        if args.command == "list":
            status = ApplicationStatus(args.status) if args.status else None
            applications = list_applications(
                store,
                status=status,
                company=args.company,
            )
            print(format_applications(applications, as_json=args.as_json))
            return 0
        if args.command == "move":
            application = transition_application(
                store,
                args.application_id,
                ApplicationStatus(args.status),
                note=args.note,
            )
            print(format_applications((application,), as_json=args.as_json, heading="Updated"))
            return 0
        if args.command == "schedule":
            application = schedule_follow_up(
                store,
                args.application_id,
                None if args.clear else args.on,
            )
            print(format_applications((application,), as_json=args.as_json, heading="Updated"))
            return 0

        if args.command == "note":
            application = add_application_note(
                store,
                args.application_id,
                args.text,
            )
            print(
                format_applications(
                    (application,),
                    as_json=args.as_json,
                    heading="Note recorded",
                )
            )
            return 0

        if args.command == "history":
            application = get_application(store, args.application_id)
            print(
                format_timeline(
                    application,
                    include_notes=args.include_notes,
                    as_json=args.as_json,
                )
            )
            return 0

        if args.command == "activity":
            since = (
                datetime.combine(args.since, time.min, tzinfo=timezone.utc)
                if args.since is not None
                else None
            )
            records = recent_activity(
                store.load(),
                since=since,
                limit=args.limit,
            )
            print(
                format_recent_activity(
                    records,
                    include_notes=args.include_notes,
                    as_json=args.as_json,
                )
            )
            return 0

        if args.command == "pipeline":
            summary = summarize_pipeline(store.load())
            print(format_pipeline(summary, as_json=args.as_json))
            return 0

        if args.command == "stale":
            applications = find_stale_applications(
                store.load(),
                as_of=args.as_of,
                inactive_days=args.inactive_days,
            )
            print(
                format_stale_applications(
                    applications,
                    as_of=args.as_of,
                    inactive_days=args.inactive_days,
                    as_json=args.as_json,
                )
            )
            return 0 if not applications else 1

        applications = due_follow_ups(store, as_of=args.as_of)
        print(
            format_due_follow_ups(
                applications,
                as_of=args.as_of,
                as_json=args.as_json,
            )
        )
        return 0 if not applications else 1
    except (ApplicationError, StorageError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
