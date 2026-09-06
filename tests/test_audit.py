from datetime import date, datetime, timezone

from applyflow.audit import AuditCode, AuditSeverity, audit_applications
from applyflow.models import Activity, Application, ApplicationStatus


NOW = datetime(2026, 9, 6, 18, 0, tzinfo=timezone.utc)


def application(**changes):
    values = {
        "id": "app-1",
        "company": "Example",
        "role": "Analyst",
        "status": ApplicationStatus.APPLIED,
        "applied_on": date(2026, 9, 1),
        "created_at": NOW,
        "updated_at": NOW,
        "history": (
            Activity(at=NOW, status=ApplicationStatus.APPLIED, note="Created"),
        ),
    }
    values.update(changes)
    return Application(**values)


def codes(result):
    return [item.code for item in result.findings]


def test_clean_record_has_healthy_audit_result():
    result = audit_applications((application(),), as_of=date(2026, 9, 6))

    assert result.healthy is True
    assert result.records_checked == 1
    assert result.error_count == 0
    assert result.warning_count == 0


def test_missing_history_is_an_error():
    result = audit_applications(
        (application(history=()),),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.MISSING_HISTORY]
    assert result.findings[0].severity == AuditSeverity.ERROR
    assert result.healthy is False


def test_current_status_must_match_latest_history():
    result = audit_applications(
        (application(status=ApplicationStatus.INTERVIEWING),),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.STATUS_HISTORY_MISMATCH]


def test_update_cannot_precede_creation():
    result = audit_applications(
        (
            application(
                created_at=datetime(2026, 9, 6, 18, 0, tzinfo=timezone.utc),
                updated_at=datetime(2026, 9, 5, 18, 0, tzinfo=timezone.utc),
            ),
        ),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.UPDATED_BEFORE_CREATED]
