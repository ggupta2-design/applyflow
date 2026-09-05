import json
from datetime import date, datetime, timezone

from applyflow.models import Activity, Application, ApplicationStatus
from applyflow.report import format_weekly_review
from applyflow.review import build_weekly_review


def _review():
    timestamp = datetime(2026, 9, 5, tzinfo=timezone.utc)
    application = Application(
        id="private-id",
        company="Private Company",
        role="Private Role",
        status=ApplicationStatus.INTERVIEWING,
        source_url="https://example.com/private",
        applied_on=date(2026, 9, 2),
        follow_up_on=date(2026, 9, 8),
        created_at=timestamp,
        updated_at=timestamp,
        history=(
            Activity(
                at=timestamp,
                status=ApplicationStatus.INTERVIEWING,
                note="Private recruiter note",
            ),
        ),
    )
    return application, build_weekly_review(
        (application,),
        ending_on=date(2026, 9, 5),
        target_submissions=4,
    )


def test_formats_readable_weekly_metrics_and_goal():
    _, review = _review()

    text = format_weekly_review(review)

    assert "Weekly review: 2026-08-30 to 2026-09-05" in text
    assert "Applications submitted: 1" in text
    assert "Interviews reached: 1" in text
    assert "Follow-ups in next 7 days: 1" in text
    assert "Submission goal: 1/4 (25.0%)" in text


def test_formats_machine_readable_weekly_metrics():
    _, review = _review()

    payload = json.loads(format_weekly_review(review, as_json=True))

    assert payload["starts_on"] == "2026-08-30"
    assert payload["ends_on"] == "2026-09-05"
    assert payload["submitted"] == 1
    assert payload["target_progress_percent"] == 25.0
    assert payload["remaining_to_target"] == 3


def test_weekly_reports_never_expose_application_details():
    application, review = _review()

    text = format_weekly_review(review)
    json_text = format_weekly_review(review, as_json=True)

    for private_value in (
        application.id,
        application.company,
        application.role,
        application.source_url,
        application.history[0].note,
    ):
        assert private_value not in text
        assert private_value not in json_text
