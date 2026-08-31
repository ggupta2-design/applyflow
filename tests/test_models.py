from datetime import date, datetime, timezone

import pytest

from applyflow.models import (
    Activity,
    Application,
    ApplicationError,
    ApplicationStatus,
    application_from_dict,
    application_to_dict,
    validate_url,
)


def sample_application():
    now = datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc)
    return Application(
        id="app-1",
        company="Example Co",
        role="Data Analyst",
        status=ApplicationStatus.APPLIED,
        source_url="https://example.com/jobs/1",
        applied_on=date(2026, 8, 31),
        follow_up_on=date(2026, 9, 7),
        created_at=now,
        updated_at=now,
        history=(Activity(at=now, status=ApplicationStatus.APPLIED, note="Created"),),
    )


def test_application_round_trip_is_lossless():
    application = sample_application()
    assert application_from_dict(application_to_dict(application)) == application


@pytest.mark.parametrize("url", ["example.com/job", "ftp://example.com/job", ""])
def test_rejects_unsafe_or_incomplete_source_urls(url):
    with pytest.raises(ApplicationError, match="http or https"):
        validate_url(url)


def test_rejects_unknown_record_fields():
    payload = application_to_dict(sample_application())
    payload["token"] = "must-not-be-accepted"
    with pytest.raises(ApplicationError, match="missing or unknown"):
        application_from_dict(payload)


def test_rejects_invalid_status_values():
    payload = application_to_dict(sample_application())
    payload["status"] = "waiting"
    with pytest.raises(ApplicationError, match="invalid values"):
        application_from_dict(payload)
