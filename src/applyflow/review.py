"""Read-only weekly progress reviews for application workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from .models import Application, ApplicationStatus


@dataclass(frozen=True)
class WeeklyReview:
    """Count-only progress metrics for one inclusive seven-day window."""

    starts_on: date
    ends_on: date
    total_records: int
    active_records: int
    created: int
    submitted: int
    interviewed: int
    offers: int
    closed: int
    activity_count: int
    overdue_follow_ups: int
    follow_ups_next_7_days: int


_TERMINAL = {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}


def _in_window(value: date, starts_on: date, ends_on: date) -> bool:
    return starts_on <= value <= ends_on


def _reached_in_window(
    application: Application,
    statuses: set[ApplicationStatus],
    *,
    starts_on: date,
    ends_on: date,
) -> bool:
    return any(
        activity.status in statuses
        and _in_window(activity.at.date(), starts_on, ends_on)
        for activity in application.history
    )


def build_weekly_review(
    applications: Iterable[Application],
    *,
    ending_on: date,
) -> WeeklyReview:
    """Summarize progress without changing or exposing individual records."""

    records = tuple(applications)
    starts_on = ending_on - timedelta(days=6)
    return WeeklyReview(
        starts_on=starts_on,
        ends_on=ending_on,
        total_records=len(records),
        active_records=sum(item.status not in _TERMINAL for item in records),
        created=sum(
            _in_window(item.created_at.date(), starts_on, ending_on)
            for item in records
        ),
        submitted=sum(
            (
                item.applied_on is not None
                and _in_window(item.applied_on, starts_on, ending_on)
            )
            or _reached_in_window(
                item,
                {ApplicationStatus.APPLIED},
                starts_on=starts_on,
                ends_on=ending_on,
            )
            for item in records
        ),
        interviewed=sum(
            _reached_in_window(
                item,
                {ApplicationStatus.INTERVIEWING},
                starts_on=starts_on,
                ends_on=ending_on,
            )
            for item in records
        ),
        offers=sum(
            _reached_in_window(
                item,
                {ApplicationStatus.OFFER},
                starts_on=starts_on,
                ends_on=ending_on,
            )
            for item in records
        ),
        closed=sum(
            _reached_in_window(
                item,
                _TERMINAL,
                starts_on=starts_on,
                ends_on=ending_on,
            )
            for item in records
        ),
        overdue_follow_ups=sum(
            item.status not in _TERMINAL
            and item.follow_up_on is not None
            and item.follow_up_on <= ending_on
            for item in records
        ),
        follow_ups_next_7_days=sum(
            item.status not in _TERMINAL
            and item.follow_up_on is not None
            and ending_on < item.follow_up_on <= ending_on + timedelta(days=7)
            for item in records
        ),
        activity_count=sum(
            _in_window(activity.at.date(), starts_on, ending_on)
            for item in records
            for activity in item.history
        ),
    )
