"""Read-only views over append-only application activity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .models import Activity, Application, ApplicationError


@dataclass(frozen=True)
class ActivityRecord:
    """One activity entry with the minimum application context needed for review."""

    application_id: str
    company: str
    role: str
    activity: Activity


def _utc(value: datetime) -> datetime:
    """Normalize timestamps for safe comparisons while preserving stored values."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def application_timeline(application: Application) -> tuple[Activity, ...]:
    """Return an application's activities in stable chronological order."""

    indexed = enumerate(application.history)
    return tuple(
        activity
        for _, activity in sorted(
            indexed,
            key=lambda item: (_utc(item[1].at), item[0]),
        )
    )


def recent_activity(
    applications: Iterable[Application],
    *,
    since: datetime | None = None,
    limit: int = 50,
) -> tuple[ActivityRecord, ...]:
    """Return the newest activity across applications with explicit bounds."""

    if isinstance(limit, bool) or limit <= 0:
        raise ApplicationError("limit must be a positive integer")

    threshold = _utc(since) if since is not None else None
    records = [
        ActivityRecord(
            application_id=application.id,
            company=application.company,
            role=application.role,
            activity=activity,
        )
        for application in applications
        for activity in application_timeline(application)
        if threshold is None or _utc(activity.at) >= threshold
    ]
    records.sort(
        key=lambda item: (
            _utc(item.activity.at),
            item.application_id,
            item.activity.status.value,
        ),
        reverse=True,
    )
    return tuple(records[:limit])
