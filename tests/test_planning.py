from datetime import date, datetime, timezone

import pytest

from applyflow.models import Application, ApplicationStatus
from applyflow.planning import ActionKind, build_action_plan


NOW = datetime(2026, 9, 3, 18, 0, tzinfo=timezone.utc)
AS_OF = date(2026, 9, 3)


def _application(
    application_id: str,
    *,
    follow_up_on: date | None,
    status: ApplicationStatus = ApplicationStatus.APPLIED,
) -> Application:
    return Application(
        id=application_id,
        company=f"Company {application_id}",
        role="Analyst",
        status=status,
        follow_up_on=follow_up_on,
        created_at=NOW,
        updated_at=NOW,
    )


def test_prioritizes_overdue_due_and_upcoming_follow_ups():
    records = (
        _application("upcoming", follow_up_on=date(2026, 9, 6)),
        _application("due", follow_up_on=AS_OF),
        _application("overdue", follow_up_on=date(2026, 9, 1)),
        _application("outside", follow_up_on=date(2026, 9, 11)),
    )

    plan = build_action_plan(records, as_of=AS_OF, horizon_days=7)

    assert [item.kind for item in plan.items] == [
        ActionKind.OVERDUE_FOLLOW_UP,
        ActionKind.DUE_TODAY,
        ActionKind.UPCOMING_FOLLOW_UP,
    ]
    assert [item.days_until for item in plan.items] == [-2, 0, 3]
    assert plan.total_candidates == 3
    assert plan.truncated is False


def test_excludes_terminal_and_unscheduled_applications():
    records = (
        _application("none", follow_up_on=None),
        _application(
            "rejected",
            follow_up_on=AS_OF,
            status=ApplicationStatus.REJECTED,
        ),
        _application(
            "withdrawn",
            follow_up_on=AS_OF,
            status=ApplicationStatus.WITHDRAWN,
        ),
    )

    assert build_action_plan(records, as_of=AS_OF).items == ()


def test_bounds_plan_and_reports_truncation():
    records = (
        _application("b", follow_up_on=AS_OF),
        _application("a", follow_up_on=AS_OF),
    )

    plan = build_action_plan(records, as_of=AS_OF, limit=1)

    assert len(plan.items) == 1
    assert plan.total_candidates == 2
    assert plan.truncated is True


@pytest.mark.parametrize(
    ("argument", "value", "message"),
    [
        ("horizon_days", -1, "non-negative integer"),
        ("inactive_days", 0, "positive integer"),
        ("limit", 0, "positive integer"),
    ],
)
def test_rejects_invalid_plan_thresholds(argument, value, message):
    options = {argument: value}

    with pytest.raises(ValueError, match=message):
        build_action_plan((), as_of=AS_OF, **options)
