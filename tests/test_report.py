import json
from datetime import date, datetime, timezone

from applyflow.models import Activity, Application, ApplicationStatus
from applyflow.report import format_applications, format_due_follow_ups


def test_formats_readable_and_json_application_summaries():
    now = datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc)
    secret_note = "Recruiter private email: person@example.com"
    application = Application(
        id="app-1",
        company="Example",
        role="Analyst",
        status=ApplicationStatus.APPLIED,
        source_url="https://example.com/private-link",
        applied_on=date(2026, 8, 31),
        follow_up_on=date(2026, 9, 7),
        created_at=now,
        updated_at=now,
        history=(Activity(at=now, status=ApplicationStatus.APPLIED, note=secret_note),),
    )

    text = format_applications((application,))
    assert "Example | Analyst | applied" in text
    payload = json.loads(format_applications((application,), as_json=True))
    assert payload["count"] == 1
    assert payload["applications"][0]["follow_up_on"] == "2026-09-07"
    assert secret_note not in text
    assert secret_note not in json.dumps(payload)
    assert application.source_url not in text
    assert application.source_url not in json.dumps(payload)


def test_formats_empty_and_due_reports():
    assert "Results: none" in format_applications(())
    payload = json.loads(
        format_due_follow_ups((), as_of=date(2026, 9, 1), as_json=True)
    )
    assert payload == {
        "applications": [],
        "as_of": "2026-09-01",
        "count": 0,
    }
