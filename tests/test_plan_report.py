import json
from datetime import date, datetime, timezone

from applyflow.models import Activity, Application, ApplicationStatus
from applyflow.planning import build_action_plan
from applyflow.report import format_action_plan


AS_OF = date(2026, 9, 3)


def _application(
    application_id: str,
    *,
    company: str,
    follow_up_on: date | None = None,
    updated_at: datetime | None = None,
) -> Application:
    timestamp = updated_at or datetime(2026, 9, 3, tzinfo=timezone.utc)
    return Application(
        id=application_id,
        company=company,
        role="Analyst",
        status=ApplicationStatus.APPLIED,
        source_url="https://example.com/private",
        follow_up_on=follow_up_on,
        created_at=timestamp,
        updated_at=timestamp,
        history=(
            Activity(
                at=timestamp,
                status=ApplicationStatus.APPLIED,
                note="Private recruiter details",
            ),
        ),
    )


def test_formats_readable_action_reasons():
    records = (
        _application(
            "overdue",
            company="Older",
            follow_up_on=date(2026, 9, 1),
        ),
        _application(
            "upcoming",
            company="Soon",
            follow_up_on=date(2026, 9, 5),
        ),
        _application(
            "stale",
            company="Quiet",
            updated_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        ),
    )
    plan = build_action_plan(records, as_of=AS_OF)

    text = format_action_plan(plan)

    assert "follow-up overdue by 2 day(s)" in text
    assert "follow-up due in 2 day(s)" in text
    assert "inactive for 33 day(s)" in text


def test_formats_bounded_json_plan_metadata():
    records = (
        _application("a", company="One", follow_up_on=AS_OF),
        _application("b", company="Two", follow_up_on=AS_OF),
    )
    plan = build_action_plan(records, as_of=AS_OF, limit=1)

    payload = json.loads(format_action_plan(plan, as_json=True))

    assert payload["count"] == 1
    assert payload["total_candidates"] == 2
    assert payload["truncated"] is True
    assert payload["actions"][0]["kind"] == "due_today"


def test_action_plan_never_exposes_urls_or_notes():
    application = _application(
        "private",
        company="Example",
        follow_up_on=AS_OF,
    )
    plan = build_action_plan((application,), as_of=AS_OF)

    text = format_action_plan(plan)
    json_text = format_action_plan(plan, as_json=True)

    assert application.source_url not in text
    assert application.source_url not in json_text
    assert application.history[0].note not in text
    assert application.history[0].note not in json_text


def test_formats_empty_action_plan():
    plan = build_action_plan((), as_of=AS_OF)

    assert "Results: none" in format_action_plan(plan)
    assert json.loads(format_action_plan(plan, as_json=True))["actions"] == []
