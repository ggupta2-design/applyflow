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

    assert AuditCode.UPDATED_BEFORE_CREATED in codes(result)
    assert AuditCode.ACTIVITY_OUTSIDE_RECORD_WINDOW in codes(result)


def test_illegal_status_jump_is_reported_once():
    history = (
        Activity(at=NOW, status=ApplicationStatus.SAVED),
        Activity(
            at=datetime(2026, 9, 6, 19, 0, tzinfo=timezone.utc),
            status=ApplicationStatus.OFFER,
        ),
    )
    result = audit_applications(
        (
            application(
                status=ApplicationStatus.OFFER,
                updated_at=history[-1].at,
                history=history,
            ),
        ),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.INVALID_STATUS_TRANSITION]


def test_same_status_note_activity_is_valid():
    history = (
        Activity(at=NOW, status=ApplicationStatus.APPLIED),
        Activity(
            at=datetime(2026, 9, 6, 19, 0, tzinfo=timezone.utc),
            status=ApplicationStatus.APPLIED,
            note="Private note",
        ),
    )
    result = audit_applications(
        (application(updated_at=history[-1].at, history=history),),
        as_of=date(2026, 9, 6),
    )

    assert result.healthy is True


def test_naive_timestamps_are_reported_without_comparison_errors():
    naive = datetime(2026, 9, 6, 18, 0)
    result = audit_applications(
        (
            application(
                created_at=naive,
                updated_at=naive,
                history=(Activity(at=naive, status=ApplicationStatus.APPLIED),),
            ),
        ),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.TIMESTAMP_WITHOUT_TIMEZONE]


def test_out_of_order_activity_is_detected():
    later = datetime(2026, 9, 6, 20, 0, tzinfo=timezone.utc)
    earlier = datetime(2026, 9, 6, 19, 0, tzinfo=timezone.utc)
    result = audit_applications(
        (
            application(
                updated_at=later,
                history=(
                    Activity(at=NOW, status=ApplicationStatus.APPLIED),
                    Activity(at=later, status=ApplicationStatus.APPLIED),
                    Activity(at=earlier, status=ApplicationStatus.APPLIED),
                ),
            ),
        ),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.ACTIVITY_OUT_OF_ORDER]


def test_future_record_and_application_dates_are_warnings():
    result = audit_applications(
        (application(applied_on=date(2026, 9, 7)),),
        as_of=date(2026, 9, 5),
    )

    assert set(codes(result)) == {
        AuditCode.FUTURE_APPLIED_DATE,
        AuditCode.FUTURE_TIMESTAMP,
    }
    assert result.error_count == 0
    assert result.warning_count == 2


def test_submitted_records_require_an_applied_date():
    result = audit_applications(
        (application(applied_on=None),),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.MISSING_APPLIED_DATE]


def test_terminal_records_cannot_keep_follow_ups():
    closed_at = datetime(2026, 9, 6, 19, 0, tzinfo=timezone.utc)
    history = (
        Activity(at=NOW, status=ApplicationStatus.APPLIED),
        Activity(at=closed_at, status=ApplicationStatus.REJECTED),
    )
    result = audit_applications(
        (
            application(
                status=ApplicationStatus.REJECTED,
                follow_up_on=date(2026, 9, 8),
                updated_at=closed_at,
                history=history,
            ),
        ),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.TERMINAL_FOLLOW_UP]


def test_duplicate_active_opportunities_are_warnings():
    result = audit_applications(
        (
            application(id="first"),
            application(id="second"),
        ),
        as_of=date(2026, 9, 6),
    )

    assert codes(result) == [AuditCode.DUPLICATE_ACTIVE_OPPORTUNITY]
    assert result.warning_count == 1


def test_terminal_duplicates_do_not_trigger_active_duplicate_warning():
    closed_at = datetime(2026, 9, 6, 19, 0, tzinfo=timezone.utc)
    history = (
        Activity(at=NOW, status=ApplicationStatus.APPLIED),
        Activity(at=closed_at, status=ApplicationStatus.REJECTED),
    )
    first = application(
        id="first",
        status=ApplicationStatus.REJECTED,
        updated_at=closed_at,
        history=history,
    )
    second = application(
        id="second",
        status=ApplicationStatus.REJECTED,
        updated_at=closed_at,
        history=history,
    )

    result = audit_applications((first, second), as_of=date(2026, 9, 6))

    assert result.healthy is True
