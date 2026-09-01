from datetime import date, datetime, timezone

from applyflow.analytics import summarize_pipeline
from applyflow.models import Activity, Application, ApplicationStatus


NOW = datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc)


def application(
    application_id,
    status,
    *,
    applied=False,
    history=(),
):
    return Application(
        id=application_id,
        company="Example",
        role=f"Role {application_id}",
        status=status,
        applied_on=date(2026, 8, 20) if applied else None,
        created_at=NOW,
        updated_at=NOW,
        history=history,
    )


def test_summarizes_current_stages_and_conversions():
    records = (
        application("saved", ApplicationStatus.SAVED),
        application("applied", ApplicationStatus.APPLIED, applied=True),
        application(
            "rejected-after-interview",
            ApplicationStatus.REJECTED,
            applied=True,
            history=(
                Activity(at=NOW, status=ApplicationStatus.INTERVIEWING),
                Activity(at=NOW, status=ApplicationStatus.REJECTED),
            ),
        ),
        application(
            "offer",
            ApplicationStatus.OFFER,
            applied=True,
            history=(Activity(at=NOW, status=ApplicationStatus.INTERVIEWING),),
        ),
        application("withdrawn", ApplicationStatus.WITHDRAWN, applied=True),
    )

    summary = summarize_pipeline(records)
    assert (summary.total, summary.active, summary.terminal) == (5, 3, 2)
    assert summary.submitted == 4
    assert summary.reached_interview == 2
    assert summary.reached_offer == 1
    assert summary.interview_rate == 50.0
    assert summary.offer_rate == 25.0
    assert {item.status.value: item.count for item in summary.status_counts} == {
        "saved": 1,
        "applied": 1,
        "interviewing": 0,
        "offer": 1,
        "rejected": 1,
        "withdrawn": 1,
    }


def test_empty_pipeline_has_zero_safe_rates():
    summary = summarize_pipeline(())
    assert summary.total == 0
    assert summary.interview_rate == 0.0
    assert summary.offer_rate == 0.0
