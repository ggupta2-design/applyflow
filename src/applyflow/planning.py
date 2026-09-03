"""Read-only daily action planning for application workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Iterable

from .models import Application, ApplicationStatus


class ActionKind(str, Enum):
    """Supported reasons an application needs attention."""

    OVERDUE_FOLLOW_UP = "overdue_follow_up"
    DUE_TODAY = "due_today"
    UPCOMING_FOLLOW_UP = "upcoming_follow_up"


@dataclass(frozen=True)
class ActionItem:
    """One prioritized, non-mutating application review item."""

    kind: ActionKind
    application: Application
    target_on: date
    days_until: int


@dataclass(frozen=True)
class ActionPlan:
    """A bounded daily review plan."""

    as_of: date
    horizon_days: int
    inactive_days: int
    total_candidates: int
    truncated: bool
    items: tuple[ActionItem, ...]


_PRIORITY = {
    ActionKind.OVERDUE_FOLLOW_UP: 0,
    ActionKind.DUE_TODAY: 1,
    ActionKind.UPCOMING_FOLLOW_UP: 2,
}


def _validate_thresholds(
    *,
    horizon_days: int,
    inactive_days: int,
    limit: int,
) -> None:
    if isinstance(horizon_days, bool) or horizon_days < 0:
        raise ValueError("horizon_days must be a non-negative integer")
    if isinstance(inactive_days, bool) or inactive_days < 1:
        raise ValueError("inactive_days must be a positive integer")
    if isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer")


def build_action_plan(
    applications: Iterable[Application],
    *,
    as_of: date,
    horizon_days: int = 7,
    inactive_days: int = 14,
    limit: int = 25,
) -> ActionPlan:
    """Build a deterministic plan without changing application records."""

    _validate_thresholds(
        horizon_days=horizon_days,
        inactive_days=inactive_days,
        limit=limit,
    )
    horizon = as_of + timedelta(days=horizon_days)
    terminal = {ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN}
    items: list[ActionItem] = []

    for application in applications:
        follow_up = application.follow_up_on
        if application.status in terminal or follow_up is None or follow_up > horizon:
            continue
        days_until = (follow_up - as_of).days
        if days_until < 0:
            kind = ActionKind.OVERDUE_FOLLOW_UP
        elif days_until == 0:
            kind = ActionKind.DUE_TODAY
        else:
            kind = ActionKind.UPCOMING_FOLLOW_UP
        items.append(
            ActionItem(
                kind=kind,
                application=application,
                target_on=follow_up,
                days_until=days_until,
            )
        )

    items.sort(
        key=lambda item: (
            _PRIORITY[item.kind],
            item.target_on,
            item.application.company.casefold(),
            item.application.role.casefold(),
            item.application.id,
        )
    )
    total = len(items)
    return ActionPlan(
        as_of=as_of,
        horizon_days=horizon_days,
        inactive_days=inactive_days,
        total_candidates=total,
        truncated=total > limit,
        items=tuple(items[:limit]),
    )
