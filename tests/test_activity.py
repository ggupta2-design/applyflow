from datetime import datetime, timedelta, timezone

import pytest

from applyflow.activity import application_timeline, recent_activity
from applyflow.models import Activity, Application, ApplicationError, ApplicationStatus


NOW = datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc)


def _application(application_id: str, activities: tuple[Activity, ...]) -> Application:
    return Application(
        id=application_id,
        company=f"Company {application_id}",
        role="Analyst",
        created_at=NOW,
        updated_at=NOW,
        history=activities,
    )


def test_timeline_is_chronological_and_stable_for_equal_timestamps():
    later = Activity(at=NOW, status=ApplicationStatus.APPLIED, note="later")
    earlier = Activity(
        at=NOW - timedelta(days=1),
        status=ApplicationStatus.SAVED,
        note="earlier",
    )
    same_time = Activity(at=NOW, status=ApplicationStatus.INTERVIEWING, note="same")

    assert application_timeline(_application("one", (later, earlier, same_time))) == (
        earlier,
        later,
        same_time,
    )


def test_recent_activity_is_newest_first_and_bounded():
    first = _application(
        "one",
        (
            Activity(
                at=NOW - timedelta(days=2),
                status=ApplicationStatus.SAVED,
            ),
            Activity(at=NOW, status=ApplicationStatus.APPLIED),
        ),
    )
    second = _application(
        "two",
        (
            Activity(
                at=NOW - timedelta(days=1),
                status=ApplicationStatus.INTERVIEWING,
            ),
        ),
    )

    records = recent_activity((first, second), limit=2)

    assert [(item.application_id, item.activity.status) for item in records] == [
        ("one", ApplicationStatus.APPLIED),
        ("two", ApplicationStatus.INTERVIEWING),
    ]


def test_recent_activity_filters_since_inclusive_and_handles_naive_dates():
    application = _application(
        "one",
        (
            Activity(
                at=(NOW - timedelta(days=1)).replace(tzinfo=None),
                status=ApplicationStatus.SAVED,
            ),
            Activity(at=NOW, status=ApplicationStatus.APPLIED),
        ),
    )

    records = recent_activity(
        (application,),
        since=NOW - timedelta(days=1),
    )

    assert len(records) == 2


@pytest.mark.parametrize("limit", [0, -1, False])
def test_recent_activity_rejects_invalid_limits(limit):
    with pytest.raises(ApplicationError, match="positive integer"):
        recent_activity((), limit=limit)
