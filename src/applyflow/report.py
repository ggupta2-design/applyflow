"""Readable and JSON reports for application workflows."""

from __future__ import annotations

import json
from datetime import date
from typing import Iterable

from .models import Application


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
