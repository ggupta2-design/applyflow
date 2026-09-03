"""Readable and JSON reports for application workflows."""

from __future__ import annotations

import json
from datetime import date
from typing import Iterable

from .activity import ActivityRecord, application_timeline
from .analytics import PipelineSummary, StaleApplication
from .models import Application
from .planning import ActionKind, ActionPlan


def application_summary(application: Application) -> dict[str, object]:
    """Return a stable summary without URLs or activity notes."""

    return {
        "id": application.id,
        "company": application.company,
        "role": application.role,
        "status": application.status.value,
        "applied_on": application.applied_on.isoformat() if application.applied_on else None,
        "follow_up_on": (
            application.follow_up_on.isoformat() if application.follow_up_on else None
        ),
        "updated_at": application.updated_at.isoformat(),
    }


def format_applications(
    applications: Iterable[Application],
    *,
    as_json: bool = False,
    heading: str = "Applications",
) -> str:
    """Format deterministic summaries for people or automation."""

    records = tuple(applications)
    payload = {
        "count": len(records),
        "applications": [application_summary(item) for item in records],
    }
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [f"{heading}: {len(records)}"]
    if not records:
        lines.append("Results: none")
        return "\n".join(lines)
    for item in records:
        follow_up = (
            f", follow up {item.follow_up_on.isoformat()}"
            if item.follow_up_on
            else ""
        )
        lines.append(
            f"- {item.id} | {item.company} | {item.role} | "
            f"{item.status.value}{follow_up}"
        )
    return "\n".join(lines)


def format_due_follow_ups(
    applications: Iterable[Application],
    *,
    as_of: date,
    as_json: bool = False,
) -> str:
    """Format due follow-ups with an explicit review date."""

    records = tuple(applications)
    if as_json:
        return json.dumps(
            {
                "as_of": as_of.isoformat(),
                "count": len(records),
                "applications": [application_summary(item) for item in records],
            },
            indent=2,
            sort_keys=True,
        )
    return format_applications(
        records,
        heading=f"Follow-ups due by {as_of.isoformat()}",
    )



def format_pipeline(summary: PipelineSummary, *, as_json: bool = False) -> str:
    """Format pipeline metrics without exposing URLs or activity notes."""

    payload = {
        "total": summary.total,
        "active": summary.active,
        "terminal": summary.terminal,
        "submitted": summary.submitted,
        "reached_interview": summary.reached_interview,
        "reached_offer": summary.reached_offer,
        "interview_rate": round(summary.interview_rate, 1),
        "offer_rate": round(summary.offer_rate, 1),
        "status_counts": {
            item.status.value: item.count for item in summary.status_counts
        },
    }
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [
        "Application pipeline",
        f"Total: {summary.total}",
        f"Active: {summary.active}",
        f"Terminal: {summary.terminal}",
        f"Submitted: {summary.submitted}",
        f"Reached interview: {summary.reached_interview} "
        f"({summary.interview_rate:.1f}%)",
        f"Reached offer: {summary.reached_offer} ({summary.offer_rate:.1f}%)",
        "Current stages:",
    ]
    lines.extend(
        f"- {item.status.value}: {item.count}" for item in summary.status_counts
    )
    return "\n".join(lines)


def format_stale_applications(
    applications: Iterable[StaleApplication],
    *,
    as_of: date,
    inactive_days: int,
    as_json: bool = False,
) -> str:
    """Format stale active records for a deliberate manual review."""

    records = tuple(applications)
    payload = {
        "as_of": as_of.isoformat(),
        "inactive_days": inactive_days,
        "count": len(records),
        "applications": [
            {
                **application_summary(item.application),
                "inactive_days": item.inactive_days,
            }
            for item in records
        ],
    }
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [
        f"Stale applications as of {as_of.isoformat()}: {len(records)}",
        f"Threshold: {inactive_days} inactive day(s)",
    ]
    if not records:
        lines.append("Results: none")
        return "\n".join(lines)
    for item in records:
        application = item.application
        lines.append(
            f"- {application.id} | {application.company} | {application.role} | "
            f"{application.status.value} | inactive {item.inactive_days} day(s)"
        )
    return "\n".join(lines)


def _activity_summary(
    *,
    at: object,
    status: str,
    note: str | None,
    include_notes: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "at": at.isoformat(),
        "status": status,
    }
    if include_notes:
        payload["note"] = note
    return payload


def format_timeline(
    application: Application,
    *,
    include_notes: bool = False,
    as_json: bool = False,
) -> str:
    """Format one timeline while withholding notes by default."""

    activities = application_timeline(application)
    payload = {
        "application": application_summary(application),
        "notes_included": include_notes,
        "count": len(activities),
        "activity": [
            _activity_summary(
                at=item.at,
                status=item.status.value,
                note=item.note,
                include_notes=include_notes,
            )
            for item in activities
        ],
    }
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [
        f"Activity for {application.id}: {len(activities)}",
        f"{application.company} | {application.role}",
        f"Notes: {'included' if include_notes else 'hidden'}",
    ]
    for item in activities:
        line = f"- {item.at.isoformat()} | {item.status.value}"
        if include_notes and item.note is not None:
            line += f" | {item.note}"
        lines.append(line)
    return "\n".join(lines)


def format_recent_activity(
    records: Iterable[ActivityRecord],
    *,
    include_notes: bool = False,
    as_json: bool = False,
) -> str:
    """Format cross-application activity without leaking notes by default."""

    selected = tuple(records)
    activities = [
        {
            "application_id": item.application_id,
            "company": item.company,
            "role": item.role,
            **_activity_summary(
                at=item.activity.at,
                status=item.activity.status.value,
                note=item.activity.note,
                include_notes=include_notes,
            ),
        }
        for item in selected
    ]
    payload = {
        "notes_included": include_notes,
        "count": len(selected),
        "activity": activities,
    }
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [
        f"Recent activity: {len(selected)}",
        f"Notes: {'included' if include_notes else 'hidden'}",
    ]
    if not selected:
        lines.append("Results: none")
    for item in selected:
        activity = item.activity
        line = (
            f"- {activity.at.isoformat()} | {item.application_id} | "
            f"{item.company} | {item.role} | {activity.status.value}"
        )
        if include_notes and activity.note is not None:
            line += f" | {activity.note}"
        lines.append(line)
    return "\n".join(lines)


def format_action_plan(plan: ActionPlan, *, as_json: bool = False) -> str:
    """Format a daily plan without source URLs or activity notes."""

    actions = [
        {
            "kind": item.kind.value,
            "application": application_summary(item.application),
            "target_on": item.target_on.isoformat(),
            "days_until": item.days_until,
            "inactive_days": item.inactive_days,
        }
        for item in plan.items
    ]
    payload = {
        "as_of": plan.as_of.isoformat(),
        "horizon_days": plan.horizon_days,
        "inactive_days": plan.inactive_days,
        "count": len(plan.items),
        "total_candidates": plan.total_candidates,
        "truncated": plan.truncated,
        "actions": actions,
    }
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)

    lines = [
        f"Daily action plan for {plan.as_of.isoformat()}: {len(plan.items)}",
        f"Planning horizon: {plan.horizon_days} day(s)",
        f"Stale threshold: {plan.inactive_days} day(s)",
    ]
    if plan.truncated:
        lines.append(
            f"Showing {len(plan.items)} of {plan.total_candidates} candidates"
        )
    if not plan.items:
        lines.append("Results: none")
        return "\n".join(lines)

    for item in plan.items:
        application = item.application
        if item.kind == ActionKind.OVERDUE_FOLLOW_UP:
            reason = f"follow-up overdue by {abs(item.days_until or 0)} day(s)"
        elif item.kind == ActionKind.DUE_TODAY:
            reason = "follow-up due today"
        elif item.kind == ActionKind.UPCOMING_FOLLOW_UP:
            reason = f"follow-up due in {item.days_until} day(s)"
        else:
            reason = f"inactive for {item.inactive_days} day(s)"
        lines.append(
            f"- {item.kind.value} | {application.id} | {application.company} | "
            f"{application.role} | {reason}"
        )
    return "\n".join(lines)
