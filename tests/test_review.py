from datetime import date, datetime, timezone

import pytest

from applyflow.models import Activity, Application, ApplicationStatus
from applyflow.review import build_weekly_review


ENDING = date(2026, 9, 5)


def _at(day: int) -> datetime:
    return datetime(2026, 9, day, 12, tzinfo=timezone.utc)


def test_summarizes_weekly_milestones_once_per_application():
    application = Application(
        id="progress",
        company="Example",
        role="Analyst",
        status=ApplicationStatus.OFFER,
        applied_on=date(2026, 9, 1),
        created_at=_at(1),
        updated_at=_at(4),
        history=(
            Activity(at=_at(1), status=ApplicationStatus.APPLIED),
            Activity(at=_at(2), status=ApplicationStatus.INTERVIEWING),
            Activity(at=_at(3), status=ApplicationStatus.INTERVIEWING),
            Activity(at=_at(4), status=ApplicationStatus.OFFER),
        ),
    )

    review = build_weekly_review((application,), ending_on=ENDING)

    assert review.starts_on == date(2026, 8, 30)
    assert review.ends_on == ENDING
    assert review.total_records == 1
    assert review.active_records == 1
    assert review.created == 1
    assert review.submitted == 1
    assert review.interviewed == 1
    assert review.offers == 1
    assert review.closed == 0
    assert review.activity_count == 4


def test_weekly_window_is_inclusive_at_both_boundaries():
    starts_on = datetime(2026, 8, 30, 23, tzinfo=timezone.utc)
    ends_on = datetime(2026, 9, 5, 23, tzinfo=timezone.utc)
    records = (
        Application(
            id="start",
            company="One",
            role="Analyst",
            created_at=starts_on,
            updated_at=starts_on,
            history=(Activity(at=starts_on, status=ApplicationStatus.SAVED),),
        ),
        Application(
            id="end",
            company="Two",
            role="Engineer",
            created_at=ends_on,
            updated_at=ends_on,
            history=(Activity(at=ends_on, status=ApplicationStatus.SAVED),),
        ),
    )

    review = build_weekly_review(records, ending_on=ENDING)

    assert review.created == 2
    assert review.activity_count == 2


def test_excludes_milestones_outside_week():
    before = datetime(2026, 8, 29, tzinfo=timezone.utc)
    application = Application(
        id="old",
        company="Example",
        role="Analyst",
        status=ApplicationStatus.REJECTED,
        applied_on=date(2026, 8, 29),
        created_at=before,
        updated_at=before,
        history=(
            Activity(at=before, status=ApplicationStatus.APPLIED),
            Activity(at=before, status=ApplicationStatus.REJECTED),
        ),
    )

    review = build_weekly_review((application,), ending_on=ENDING)

    assert review.created == 0
    assert review.submitted == 0
    assert review.closed == 0
    assert review.activity_count == 0
    assert review.active_records == 0


def test_counts_overdue_and_next_week_follow_ups():
    timestamp = _at(1)
    records = (
        Application(
            id="overdue",
            company="One",
            role="Analyst",
            status=ApplicationStatus.APPLIED,
            follow_up_on=date(2026, 9, 4),
            created_at=timestamp,
            updated_at=timestamp,
        ),
        Application(
            id="upcoming",
            company="Two",
            role="Engineer",
            status=ApplicationStatus.INTERVIEWING,
            follow_up_on=date(2026, 9, 12),
            created_at=timestamp,
            updated_at=timestamp,
        ),
        Application(
            id="outside",
            company="Three",
            role="Designer",
            status=ApplicationStatus.APPLIED,
            follow_up_on=date(2026, 9, 13),
            created_at=timestamp,
            updated_at=timestamp,
        ),
    )

    review = build_weekly_review(records, ending_on=ENDING)

    assert review.overdue_follow_ups == 1
    assert review.follow_ups_next_7_days == 1


def test_terminal_follow_ups_are_not_counted():
    timestamp = _at(1)
    application = Application(
        id="closed",
        company="Example",
        role="Analyst",
        status=ApplicationStatus.REJECTED,
        follow_up_on=ENDING,
        created_at=timestamp,
        updated_at=timestamp,
    )

    review = build_weekly_review((application,), ending_on=ENDING)

    assert review.overdue_follow_ups == 0
    assert review.follow_ups_next_7_days == 0


def test_measures_submission_goal_progress():
    records = tuple(
        Application(
            id=f"app-{index}",
            company=f"Company {index}",
            role="Analyst",
            status=ApplicationStatus.APPLIED,
            applied_on=date(2026, 9, index + 1),
            created_at=_at(index + 1),
            updated_at=_at(index + 1),
        )
        for index in range(3)
    )

    review = build_weekly_review(
        records,
        ending_on=ENDING,
        target_submissions=4,
    )

    assert review.submitted == 3
    assert review.target_submissions == 4
    assert review.remaining_to_target == 1
    assert review.target_progress_percent == 75.0


def test_caps_remaining_goal_at_zero():
    application = Application(
        id="app-1",
        company="Example",
        role="Analyst",
        status=ApplicationStatus.APPLIED,
        applied_on=ENDING,
        created_at=_at(5),
        updated_at=_at(5),
    )

    review = build_weekly_review(
        (application,),
        ending_on=ENDING,
        target_submissions=1,
    )

    assert review.remaining_to_target == 0
    assert review.target_progress_percent == 100.0


@pytest.mark.parametrize("target", [0, -1, False])
def test_rejects_invalid_submission_targets(target):
    with pytest.raises(ValueError, match="positive integer"):
        build_weekly_review(
            (),
            ending_on=ENDING,
            target_submissions=target,
        )
